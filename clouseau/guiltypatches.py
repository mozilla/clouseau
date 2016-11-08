# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
from datetime import (datetime, timedelta)
from pprint import pprint
from libmozdata import utils
import re
import copy
import pytz
import os.path
from os import listdir
import json
from collections import defaultdict
from libmozdata.FileStats import FileStats
from libmozdata import socorro
from libmozdata.connection import (Connection, Query)
import libmozdata.versions
from . import config


hg_pattern = re.compile('hg:hg.mozilla.org[^:]*:([^:]*):([a-z0-9]+)')
forbidden_dirs = {'obj-firefox'}


def is_allowed(name):
    return all(not name.startswith(d) for d in forbidden_dirs)


def get_path_node(hg_uri):
    """Get node for file name from path

    Args:
        path (str): path from socorro

    Returns:
        (str, str): filename and node
    """
    if hg_uri:
        m = hg_pattern.match(hg_uri)
        if m:
            name = m.group(1)
            node = m.group(2)
        else:
            name = hg_uri
            node = None

        return name, node

    return None, None


def get_bt(info, cache=None):
    """Get info from different backtraces

    Args:
        info (dict): signature -> uuids

    Returns:
        dict: info about the different backtraces
    """

    def handler(json, data):
        uuid = json['uuid']
        jd = json['json_dump']
        if 'threads' in jd and 'crashedThread' in json:
            thread_nb = json['crashedThread']
            if thread_nb is not None:
                frames = jd['threads'][thread_nb]['frames']
                functions = tuple(frame['function'] for frame in frames if 'function' in frame)
                if functions in data:
                    data[functions]['count'] += 1
                    data[functions]['uuids'].append(uuid)
                else:
                    files = tuple(frame.get('file', None) for frame in frames if 'function' in frame)
                    data[functions] = {'count': 1, 'uuids': [uuid], 'files': files, 'processed': False}

    data = {}
    queries = []
    cached_uuids = cache['uuids'] if cache else set()

    for sgn, uuids in info.items():
        d = {}
        data[sgn] = d
        for uuid in uuids:
            if uuid not in cached_uuids:
                print('New UUID: %s' % uuid)
                queries.append(Query(socorro.ProcessedCrash.URL, params={'crash_id': uuid}, handler=handler, handlerdata=d))
            else:
                print('Old UUID: %s' % uuid)

    if queries:
        socorro.ProcessedCrash(queries=queries).wait()

    if cache:
        cached_bt_info = cache['bt_info']
        for sgn, info in data.items():
            if sgn in cached_bt_info:
                for bt in cached_bt_info[sgn].keys():
                    if bt in info:
                        cached_bt_info[sgn][bt]['count'] += info[bt]['count']
                        cached_bt_info[sgn][bt]['uuids'].extend(info[bt]['uuids'])
                        info[bt]['processed'] = True

    return data


def walk_on_the_bt(channel, ts, max_days, info, sgn=None):
    files_info = {}
    treated = set()
    if sgn:
        print('Walk on the bt for signature %s' % sgn)

    # info is: bt->{'count', 'uuids', 'files', 'processed'}
    for i in info.values():
        if i['processed']:
            continue

        for f in i['files']:
            if f and f not in treated:
                treated.add(f)
                filename, node = get_path_node(f)
                files_info[f] = {'filename': filename, 'patches': []}
                if node and is_allowed(filename):
                    if sgn:
                        print('file %s' % filename)
                    fs = FileStats(path=filename, channel=channel, node=node, utc_ts=ts, max_days=max_days)
                    res = fs.get_last_patches()
                    if res:
                        l = [(r['node'], r['pushdate'][0]) for r in res]
                        l = sorted(l, key=lambda p: p[1], reverse=True)
                        l = [{'node': p, 'pushdate': str(utils.get_date_from_timestamp(q))} for p, q in l]
                        files_info[f]['patches'] = l

    if sgn:
        print('Walk on the bt for signature %s finished.' % sgn)

    return files_info


def get_uuids_for_spiking_signatures(channel, product='Firefox', date='today', limit=100000, max_days=3, threshold=5):
    base_versions = libmozdata.versions.get(base=True)
    versions_by_channel = socorro.ProductVersions.get_info_from_major(base_versions, product=product)
    versions = [i['version'] for i in versions_by_channel[channel]]

    end_date = utils.get_date_ymd(date)  # 2016-10-18 UTC
    end_date_moz = pytz.timezone('US/Pacific').localize(datetime(end_date.year, end_date.month, end_date.day))  # 2016-10-18 PST
    end_buildid = utils.get_buildid_from_date(end_date_moz)  # < 20161018000000
    start_date_moz = end_date_moz - timedelta(days=max_days + 1)  # 2016-10-14 PST (max_days == 3)
    start_buildid = utils.get_buildid_from_date(start_date_moz)  # >= 20161014000000
    search_buildid = ['>=' + start_buildid, '<' + end_buildid]
    start_date = utils.as_utc(start_date_moz)  # 2016-10-14 07:00:00 UTC
    search_date = '>=' + utils.get_date_str(start_date)
    data = defaultdict(lambda: defaultdict(lambda: 0))
    buildids = {}

    def handler(json, data):
        if not json['errors']:
            for facets in json['facets']['build_id']:
                date = utils.get_date_from_buildid(facets['term'])
                buildids[date] = facets['count']
                for s in facets['facets']['signature']:
                    sgn = s['term']
                    count = s['count']
                    data[sgn][date] += count

    socorro.SuperSearch(params={'product': product,
                                'version': versions,
                                'date': search_date,
                                'build_id': search_buildid,
                                'release_channel': channel,
                                '_aggs.build_id': 'signature',
                                '_facets_size': limit,
                                '_results_number': 0},
                        handler=handler, handlerdata=data).wait()

    _data = {}
    start_date = utils.as_utc(datetime(start_date.year, start_date.month, start_date.day))  # 2016-10-14 UTC
    base = {start_date + timedelta(days=i): {'buildids': {}, 'total': 0} for i in range(max_days + 1)}  # from 2016-10-14 to 2016-10-17 UTC

    for sgn, info in data.items():
        d = copy.deepcopy(base)
        _data[sgn] = d
        for bid, count in info.items():
            date = utils.as_utc(datetime(bid.year, bid.month, bid.day))
            d[date]['buildids'][bid] = count
            d[date]['total'] += count
    data = _data

    spiking_signatures = []
    for sgn, info in data.items():
        stats2 = [i['total'] for _, i in sorted(info.items(), key=lambda p: p[0])]
        if all(i == 0 for i in stats2[:-1]) and stats2[-1] >= threshold:
            spiking_signatures.append(sgn)

    data = None
    if spiking_signatures:
        pprint(spiking_signatures)

        start_buildid = utils.get_buildid_from_date(end_date_moz - timedelta(days=1))
        search_buildid = ['>=' + start_buildid, '<' + end_buildid]
        queries = []
        data = {}

        def handler(json, data):
            if not json['errors']:
                for facets in json['facets']['signature']:
                    sgn = facets['term']
                    uuids = [k['term'] for k in facets['facets']['uuid']]
                    data[sgn] = uuids

        for sgns in Connection.chunks(spiking_signatures, 10):
            queries.append(Query(socorro.SuperSearch.URL,
                                 {'product': product,
                                  'version': versions,
                                  'date': search_date,
                                  'build_id': search_buildid,
                                  'signature': ['=' + s for s in sgns],
                                  'release_channel': channel,
                                  '_aggs.signature': 'uuid',
                                  '_facets_size': 100000,
                                  '_results_number': 0},
                                 handler=handler, handlerdata=data))
        socorro.SuperSearch(queries=queries).wait()

    return data


def analyze(channel, data, date='today', max_days=3, cache=None):
    results = {}
    if data:
        bt_info = get_bt(data, cache=cache)
        ts = utils.get_timestamp(date)
        date = utils.get_date_ymd(date)

        for sgn, info1 in bt_info.items():
            res = []
            info = walk_on_the_bt(channel, ts, max_days, info1, sgn=sgn)
            for bt, info2 in info1.items():
                if not info2['processed']:
                    l = []
                    haspatch = False
                    for i in range(len(info2['files'])):
                        f = info2['files'][i]
                        if f:
                            if not haspatch and info[f]['patches']:
                                haspatch = True
                            l.append((bt[i], info[f]))
                        else:
                            l.append((bt[i], {'filename': '', 'patches': []}))
                    res.append({'count': info2['count'], 'uuids': info2['uuids'], 'haspatches': haspatch, 'bt': l})
            results[sgn] = res
    return results


def get_filename(date, output_dir):
    date = utils.get_date_str(utils.get_date_ymd(date))
    filename = os.path.join(output_dir, date + '.json')
    return filename


def get_data(date, output_dir):
    if output_dir:
        filename = get_filename(date, output_dir)
        if os.path.isfile(filename):
            with open(filename, 'r') as In:
                data = json.load(In)
                return data

    return None


def get_cache(channel, product, date, output_dir):
    data = get_data(date, output_dir)
    if data:
        # get the uuids and the bt info
        uuids = []
        bt_info = defaultdict(lambda: dict())
        if product in data and channel in data[product]:
            for sgn, results in data[product][channel].items():
                for result in results:
                    uuids.extend(result['uuids'])
                    bt = tuple(e[0] for e in result['bt'])
                    bt_info[sgn][bt] = result
            return {'uuids': set(uuids), 'bt_info': bt_info, 'data': data}
        else:
            return {'uuids': None, 'bt_info': None, 'data': data}
    return None


def put_cache(channel, product, date, output_dir, cache, results):
    if output_dir:
        if cache:
            if product in cache['data']:
                if channel in cache['data'][product]:
                    data = cache['data'][product][channel]
                    for sgn, res in results.items():
                        if sgn in data:
                            data[sgn].extend(res)
                        else:
                            data[sgn] = res
                else:
                    cache['data'][product][channel] = results
            else:
                cache['data'][product] = {channel: results}
            data = cache['data']
        else:
            data = {product: {channel: results}}

        filename = get_filename(date, output_dir)
        with open(filename, 'w') as Out:
            json.dump(data, Out, sort_keys=True)


def generate(channel='nightly', product='Firefox', date='today', max_days=3, threshold=5, output_dir=None):
    if not output_dir:
        output_dir = config.get('GuiltyPatches', 'output', None)

    cache = get_cache(channel, product, date, output_dir)
    data = get_uuids_for_spiking_signatures(channel, product=product, date=date, max_days=max_days, threshold=threshold)
    if cache and cache['uuids']:
        results = analyze(channel, data, date=date, max_days=max_days, cache=cache)
    else:
        results = analyze(channel, data, date=date, max_days=max_days)
    put_cache(channel, product, date, output_dir, cache, results)


def getdates(output_dir):
    if not output_dir:
        output_dir = config.get('GuiltyPatches', 'output', None)

    pat = re.compile('([0-9]{4}-[0-9]{2}-[0-9]{2})\.json$')
    dates = []
    for f in listdir(output_dir):
        if os.path.isfile(os.path.join(output_dir, f)):
            m = pat.match(f)
            if m:
                dates.append(m.group(1))
    return {'dates': sorted(dates, reverse=True)}


def get(channel, product, date, output_dir):
    if not channel:
        channel = 'nightly'
    if not product:
        product = 'Firefox'
    if not date:
        date = 'today'

    if not output_dir:
        output_dir = config.get('GuiltyPatches', 'output', None)

    data = get_data(date, output_dir)
    if product in data and channel in data[product]:
        return data[product][channel]
    return {}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find out the guilty patches')
    parser.add_argument('-d', '--date', action='store', default='today', help='the date')
    parser.add_argument('-o', '--output', action='store', default='', help='the output directory')
    parser.add_argument('-m', '--max', action='store', type=int, default=3, help='the number of days')
    parser.add_argument('-c', '--channel', action='store', default='nightly', help='release channel')
    parser.add_argument('-p', '--product', action='store', default='Firefox', help='the product, by default Firefox')
    parser.add_argument('-t', '--threshold', action='store', type=int, default=1, help='the threshold')

    args = parser.parse_args()

    generate(channel=args.channel, product=args.product, date=args.date, max_days=args.max, threshold=args.threshold, output_dir=args.output)
