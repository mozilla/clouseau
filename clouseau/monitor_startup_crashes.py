# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import json
import datetime
import os
import functools
import requests
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader
import libmozdata.socorro as socorro
import libmozdata.utils as utils
import libmozdata.spikeanalysis as spikeanalysis
import libmozdata.gmail as gmail


delay_by_channel = {'release': 12,
                    'beta': 4,
                    'aurora': 9,
                    'nightly': 9}
products = ['Firefox', 'FennecAndroid']
channels = ['release', 'beta', 'aurora', 'nightly']


def get_crashanalysis_data():
    data = {}
    url = 'https://crash-analysis.mozilla.com/rkaiser'
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


def monitor(emails=[], date='yesterday', path='', data=None, verbose=False):
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
    search_date_bak = search_date
    all_versions = {}
    versions_pc = defaultdict(lambda: defaultdict(lambda: []))

    def handler_ss(date, product, json, data):
        if not json['errors']:
            for info in json['facets']['release_channel']:
                chan = info['term']
                throttle = 10 if chan == 'release' else 1
                total = info['count']
                if product == 'FennecAndroid':
                    d = {'total': total}
                    if chan in data:
                        data[chan][date] = d
                    else:
                        data[chan] = {date: d}
                else:
                    total *= throttle
                    d = {'browser': 0, 'plugin': 0, 'content': 0, 'total': total}
                    for pt in info['facets']['process_type']:
                        term = pt['term']
                        count = pt['count']
                        d[term] += count * throttle
                    d['browser'] = total - (d['plugin'] + d['content'])
                    if chan in data:
                        data[chan][date] = d
                    else:
                        data[chan] = {date: d}

    for product in products:
        versions = socorro.ProductVersions.get_all_versions(product)
        all_versions[product] = []
        for chan in channels:
            info = versions[chan]
            last_ver_major = max(info.keys())
            _start_date = start_date - datetime.timedelta(weeks=delay_by_channel[chan])
            for major in range(last_ver_major, last_ver_major - 4, -1):
                for v, d in info[major]['versions'].items():
                    if not v.endswith('b') and _start_date <= d <= start_date:
                        all_versions[product].append(v)
                        versions_pc[product][chan].append(v)
        searches.append(socorro.SuperSearch(params={'product': product,
                                                    'date': search_date,
                                                    'release_channel': channels,
                                                    'version': all_versions[product],
                                                    'uptime': '<60',
                                                    '_results_number': 0,
                                                    '_facets_size': 100,
                                                    '_aggs.release_channel': 'process_type'},
                                            handler=functools.partial(handler_ss, utils.get_date_str(start_date), product), handlerdata=data[product]))

    for s in searches:
        s.wait()

    if date == 'yesterday' and path:
        with open(path, 'w') as Out:
            json.dump(data, Out, sort_keys=True)

    new_start_date = start_date - datetime.timedelta(days=1)
    search_date = socorro.SuperSearch.get_search_date(new_start_date, end_date)

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
            issp = spikeanalysis.is_spiking_ma(_data, alpha=2.5, win=7, method='mean', plot=False) == 'up'
            if issp:
                # spikeanalysis.is_spiking_ma(_data, alpha=2.5, win=7, method='mean', plot=True)
                searches.append(socorro.SuperSearch(params={'product': product,
                                                            'date': search_date,
                                                            'release_channel': chan,
                                                            'version': all_versions[product],
                                                            'uptime': '<60',
                                                            '_results_number': 0,
                                                            '_histogram.date': 'signature',
                                                            '_facets_size': 3},
                                                    handler=handler_ss_spikers, handlerdata=spikers_info[product][chan]))

    for s in searches:
        s.wait()

    if spikers_info:
        # So we've some spikes... need to send an email with all the info
        affected_chans = set()
        for p, i1 in spikers_info.items():
            for c, i2 in i1.items():
                affected_chans.add(c)
                url = socorro.SuperSearch.get_link({'product': p,
                                                    'date': search_date_bak,
                                                    'release_channel': c,
                                                    'version': versions_pc[p][c],
                                                    'uptime': '<60'})
                i1[c] = [(utils.get_date_str(d), s) for d, s in sorted(i2.items(), key=lambda p: p[0])]
                i1[c] = [(url, d, sorted(s.items(), key=lambda p: p[1], reverse=True)) for d, s in i1[c]]
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('startup_crashes_email')
        body = template.render(spikers_info=spikers_info)
        title = 'Spikes in %s' % ', '.join(affected_chans)

        if emails:
            gmail.send(emails, title, body)
        elif verbose:
            print('Title: %s' % title)
            print('Body:')
            print(body)

        return {'title': title, 'body': body}

    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update status flags in Bugzilla')
    parser.add_argument('-p', '--path', action='store', default='', help='the path of the crashes history')
    parser.add_argument('-e', '--email', dest='emails', action='store', nargs='+', default=[], help='emails')
    parser.add_argument('-d', '--date', dest='date', action='store', default='yesterday', help='emails')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose mode')
    args = parser.parse_args()

    monitor(path=os.path.expanduser(os.path.expandvars(args.path)), emails=args.emails, date=args.date, verbose=args.verbose)
