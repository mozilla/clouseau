# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import datetime
import os
import functools
import requests
from collections import (defaultdict, OrderedDict)
from jinja2 import Environment, FileSystemLoader
import libmozdata.socorro as socorro
import libmozdata.utils as utils
import libmozdata.spikeanalysis as spikeanalysis
import libmozdata.gmail as gmail
from libmozdata.bugzilla import Bugzilla
from . import statusflags
from . import config
import inflect


products = config.get('MonitorStartupCrashes', 'products', ['Firefox', 'FennecAndroid'], type=list)
channels = config.get('MonitorStartupCrashes', 'channels', ['release', 'beta', 'aurora', 'nightly'], type=list)


def get_crashanalysis_data():
    data = {}
    url = 'https://crash-analysis.mozilla.com/release-mgmt'
    for product in products:
        for chan in channels:
            jsonfile = '%s-%s-crashes-categories.json' % (product, chan)
            data[jsonfile] = requests.get(url + '/' + jsonfile).json()
    return data


def convert(data):
    new_data = {p: {c: {} for c in channels} for p in products}

    for product in products:
        for chan in channels:
            dc = new_data[product][chan]
            _data = data['%s-%s-crashes-categories.json' % (product, chan)]
            for date, info in _data.items():
                if 'startup' in info:
                    numbers = info['startup']
                    for k, v in numbers.items():
                        numbers[k] = int(v)
                    if product == 'Firefox':
                        numbers['total'] = sum(numbers.values())
                    else:
                        n = numbers['browser']
                        del numbers['browser']
                        numbers['total'] = n
                elif product == 'Firefox':
                    numbers = {'browser': 0, 'content': 0, 'plugin': 0, 'total': 0}
                else:
                    numbers = {'total': 0}
                dc[date] = numbers

    return new_data


def get_most_signifiant_increases(data):
    # Get the differences between signatures numbers
    # data = {product -> {channel -> {date -> {signature -> count...
    interesting_sgns = defaultdict(lambda: defaultdict(lambda: {}))
    infinity = float('+Inf')
    for p, i1 in data.items():
        for c, i2 in i1.items():
            # add signature -> 0 for signature which have no crash
            signatures = set(s for sgns in i2.values() for s in sgns.keys())
            for sgns in i2.values():
                for s in signatures:
                    if s not in sgns:
                        sgns[s] = 0

            diffs = {}
            for d, sgns in sorted(i2.items(), key=lambda p: p[0], reverse=True):
                for sgn, n in sgns.items():
                    if sgn in diffs:
                        if diffs[sgn][0] > n:
                            rate = int(round(100. * float(diffs[sgn][0] - n) / float(n))) if n != 0 else infinity
                            diffs[sgn] = (diffs[sgn][0] - n, diffs[sgn][0], n, rate)
                        else:
                            del diffs[sgn]
                    else:
                        diffs[sgn] = (n, n, 0, infinity)
            # we've all the diffs for a product and a channel
            s = sorted(diffs.items(), key=lambda p: p[0])
            x = [float(n[0]) for _, n in s]
            outliers = spikeanalysis.generalized_esd(x, 3, alpha=0.01, method='mean')
            if outliers:
                interesting_sgns[p][c] = {s[i][0]: s[i][1] for i in outliers}

    return interesting_sgns


def get_bugs(data):
    signatures = set()
    for p, i1 in data.items():
        for c, i2 in i1.items():
            signatures = signatures.union(set(i2.keys()))
    bugs_by_signature = socorro.Bugs.get_bugs(list(signatures))
    statusflags.reduce_set_of_bugs(bugs_by_signature)

    for s, bugs in bugs_by_signature.items():
        bugs_by_signature[s] = [(str(bug), Bugzilla.get_links(bug)) for bug in sorted(bugs, key=lambda k: int(k))]

    return bugs_by_signature


def monitor(emails=[], date='yesterday', path='', data=None, verbose=False, writejson=False):
    if not data:
        try:
            with open(path, 'r') as In:
                data = json.load(In)
        except IOError:
            data = {p: {c: {} for c in channels} for p in products}

    searches = []
    start_date = utils.get_date_ymd(date)
    end_date = start_date + datetime.timedelta(days=1)
    search_date = socorro.SuperSearch.get_search_date(start_date, end_date)
    all_versions = {}
    versions_pc = defaultdict(lambda: defaultdict(lambda: []))

    def handler_ss(date, product, json, data):
        if not json['errors']:
            for info in json['facets']['release_channel']:
                chan = info['term']
                total = info['count']
                if product == 'FennecAndroid':
                    d = {'total': total}
                    if chan in data:
                        data[chan][date] = d
                    else:
                        data[chan] = {date: d}
                else:
                    throttle = 10 if chan == 'release' else 1
                    total *= throttle
                    d = {'browser': 0, 'plugin': 0, 'content': 0, 'total': total}
                    for pt in info['facets']['process_type']:
                        term = pt['term']
                        count = pt['count']
                        if term in d:  # term can be 'gpu' (very rare)
                            d[term] += count * throttle
                    d['browser'] = total - (d['plugin'] + d['content'])
                    if chan in data:
                        data[chan][date] = d
                    else:
                        data[chan] = {date: d}

    if date == 'today':
        dates = ['yesterday', 'today']
    else:
        dates = [date]

    delay_by_channel = {'release': config.get('MonitorStartupCrashes', 'delay_release', 12, type=int),
                        'beta': config.get('MonitorStartupCrashes', 'delay_beta', 4, type=int),
                        'aurora': config.get('MonitorStartupCrashes', 'delay_aurora', 9, type=int),
                        'nightly': config.get('MonitorStartupCrashes', 'delay_nightly', 9, type=int)}

    for data_date in dates:
        data_date = utils.get_date_ymd(data_date)
        next_data_date = data_date + datetime.timedelta(days=1)
        search_data_date = socorro.SuperSearch.get_search_date(data_date, next_data_date)
        for product in products:
            versions = socorro.ProductVersions.get_all_versions(product)
            all_versions[product] = []
            for chan in channels:
                info = versions[chan]
                last_ver_major = max(info.keys())
                _start_date = data_date - datetime.timedelta(weeks=delay_by_channel[chan])
                for major in range(last_ver_major, last_ver_major - 4, -1):
                    for v, d in info[major]['versions'].items():
                        if not v.endswith('b') and _start_date <= d <= data_date:
                            all_versions[product].append(v)
                            versions_pc[product][chan].append(v)
            searches.append(socorro.SuperSearch(params={'product': product,
                                                        'date': search_data_date,
                                                        'release_channel': channels,
                                                        'version': all_versions[product],
                                                        'uptime': '<60',
                                                        '_results_number': 0,
                                                        '_facets_size': 100,
                                                        '_aggs.release_channel': 'process_type'},
                                                handler=functools.partial(handler_ss, utils.get_date_str(data_date), product), handlerdata=data[product]))

    for s in searches:
        s.wait()

    if writejson and path:
        with open(path, 'w') as Out:
            json.dump(data, Out, sort_keys=True)

    new_start_date = start_date - datetime.timedelta(days=1)
    new_search_date = socorro.SuperSearch.get_search_date(new_start_date, end_date)

    def handler_ss_spikers(json, data):
        if not json['errors']:
            for facets in json['facets']['histogram_date']:
                date = utils.get_date_ymd(facets['term'])
                s = facets['facets']['signature']
                d = {}
                data[date] = d
                for signature in s:
                    count = signature['count']
                    sgn = signature['term']
                    d[sgn] = count

    spikers_info = defaultdict(lambda: defaultdict(lambda: dict()))

    searches = []
    for product, i1 in data.items():
        for chan, i2 in i1.items():
            _data = [float(i[1]['total']) for i in sorted(i2.items(), key=lambda p: utils.get_date_ymd(p[0])) if utils.get_date_ymd(i[0]) <= start_date]
            # print(product, chan)
            issp = spikeanalysis.is_spiking_ma(_data, alpha=2.5, win=7, method='mean', plot=False) == 'up'
            # spikeanalysis.get_spikes_ma(_data, alpha=2.5, win=7, method='mean', plot=True)
            if issp:
                # spikeanalysis.is_spiking_ma(_data, alpha=2.5, win=7, method='mean', plot=True)
                searches.append(socorro.SuperSearch(params={'product': product,
                                                            'date': new_search_date,
                                                            'release_channel': chan,
                                                            'version': all_versions[product],
                                                            'uptime': '<60',
                                                            '_results_number': 0,
                                                            '_histogram.date': 'signature',
                                                            '_facets_size': 100},
                                                    handler=handler_ss_spikers, handlerdata=spikers_info[product][chan]))

    for s in searches:
        s.wait()

    if spikers_info:
        # So we've some spikes... need to send an email with all the info
        searches = []
        interesting_sgns = get_most_signifiant_increases(spikers_info)
        bugs_by_signature = get_bugs(interesting_sgns)
        affected_chans = set()
        crash_data = {p: {} for p in spikers_info.keys()}
        spikes_number = 0

        def handler_global(product, json, data):
            if not json['errors']:
                for info in json['facets']['release_channel']:
                    chan = info['term']
                    throttle = 10 if product == 'FennecAndroid' and chan == 'release' else 1
                    total = info['count'] * throttle
                    data[chan] = total

        for p, i1 in spikers_info.items():
            searches.append(socorro.SuperSearch(params={'product': p,
                                                        'date': search_date,
                                                        'release_channel': list(i1.keys()),
                                                        'version': all_versions[p],
                                                        '_results_number': 0,
                                                        '_facets_size': 5,
                                                        '_aggs.release_channel': 'signature'},
                                                handler=functools.partial(handler_global, p), handlerdata=crash_data[p]))

            for c in i1.keys():
                spikes_number += 1
                affected_chans.add(c)
                url = socorro.SuperSearch.get_link({'product': p,
                                                    'date': search_date,
                                                    'release_channel': c,
                                                    'version': versions_pc[p][c],
                                                    'uptime': '<60'})
                sgns_chan = interesting_sgns[p]
                sgns_stats = [(s, bugs_by_signature[s], t[2], t[1], t[3]) for s, t in sorted(sgns_chan[c].items(), key=lambda p: p[1][0], reverse=True)]
                sgns_chan[c] = (url, sgns_stats)

        for s in searches:
            s.wait()

        env = Environment(loader=FileSystemLoader('templates'))
        env.filters['inflect'] = inflect
        template = env.get_template('startup_crashes_email')
        _is = OrderedDict()
        for product in sorted(interesting_sgns.keys()):
            _is[product] = OrderedDict()
            for chan in sorted(interesting_sgns[product].keys()):
                _is[product][chan] = interesting_sgns[product][chan]
        interesting_sgns = _is

        body = template.render(spikes_number=spikes_number, spikes_number_word=inflect.engine().number_to_words(spikes_number), crash_data=crash_data, start_date=utils.get_date_str(new_start_date), end_date=utils.get_date_str(start_date), interesting_sgns=interesting_sgns)
        title = 'Spikes in startup crashes in %s' % ', '.join(affected_chans)

        if emails:
            gmail.send(emails, title, body, html=True)
        if verbose:
            print('Title: %s' % title)
            print('Body:')
            print(body)

        return {'title': title, 'body': body}

    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Monitor spikes in startup crashes')
    parser.add_argument('-p', '--path', action='store', default='', help='the path of the crashes history')
    parser.add_argument('-e', '--email', dest='emails', action='store', nargs='+', default=[], help='emails')
    parser.add_argument('-d', '--date', dest='date', action='store', default='yesterday', help='date')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    monitor(path=os.path.expanduser(os.path.expandvars(args.path)), emails=args.emails, date=args.date, verbose=args.verbose, writejson=True)
