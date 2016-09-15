# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
from libmozdata.bugzilla import Bugzilla
from libmozdata.hgmozilla import Mercurial
import libmozdata.socorro as socorro
import libmozdata.utils as utils
import responses
from tests.auto_mock import MockTestCase
from clouseau import statusflags


class StatusFlagTest(MockTestCase):
    mock_urls = [
        Bugzilla.URL,
        socorro.Socorro.CRASH_STATS_URL,
        Mercurial.HG_URL
    ]

    @responses.activate
    def test_get_bugs_info(self):
        status_flags = Bugzilla.get_status_flags()
        bugs = ['701227', '701232']
        info = statusflags.get_bugs_info(bugs, status_flags)
        self.assertEqual(set(info.keys()), set(bugs))
        info1 = info[bugs[0]]
        self.assertEqual(info1['assigned'], True)
        self.assertEqual(info1['fixed'], True)
        self.assertEqual(info1['incomplete'], False)
        self.assertEqual(info1['no_change'], set())
        self.assertEqual(info1['patched'], True)
        self.assertEqual(info1['resolved'], False)
        self.assertEqual(info1['fixed_dates'][0], utils.get_date_ymd('2011-11-11 10:26:06'))
        self.assertEqual(info1['last_change'], utils.get_date_ymd('2013-01-14 16:31:50'))
        info2 = info[bugs[1]]
        self.assertEqual(info2['assigned'], True)
        self.assertEqual(info2['fixed'], True)
        self.assertEqual(info2['incomplete'], False)
        self.assertEqual(info2['no_change'], set())
        self.assertEqual(info2['patched'], False)
        self.assertEqual(info2['resolved'], True)
        self.assertEqual(info2['fixed_dates'][0], utils.get_date_ymd('2011-11-10 03:13:31'))
        self.assertEqual(info2['last_change'], utils.get_date_ymd('2015-03-12 15:17:16'))

        bugs = ['844479']
        fl = 'cf_status_firefox'
        info = statusflags.get_bugs_info(bugs, {'nightly': fl + '23',
                                                'aurora': fl + '22',
                                                'beta': fl + '21',
                                                'release': fl + '20'})
        self.assertEqual(set(info.keys()), set(bugs))
        info3 = info[bugs[0]]
        self.assertEqual(info3['assigned'], True)
        self.assertEqual(info3['fixed'], True)
        self.assertEqual(info3['incomplete'], False)
        self.assertEqual(info3['no_change'], {'aurora', 'beta'})
        self.assertEqual(info3['patched'], True)
        self.assertEqual(info3['resolved'], True)
        self.assertEqual(info3['fixed_dates'][0], utils.get_date_ymd('2013-08-06 21:12:03'))
        self.assertEqual(info3['last_change'], utils.get_date_ymd('2013-08-20 19:26:07'))

    @responses.activate
    def test_filter_bugs(self):
        must_stay = ['633447', '633452']
        must_leave = ['48460', '634534', '631998']
        bugs = must_stay + must_leave
        filtered = statusflags.filter_bugs(bugs, 'Firefox')
        self.assertEqual(set(map(lambda b: str(b), filtered)), set(must_stay))

    @responses.activate
    def test_get_crash_positions(self):
        def getnumbers(b, c, p):
            return {'browser': b, 'content': c, 'plugin': p}

        search, data = statusflags.get_crash_positions(100, 'Firefox', {'release': ['48.0', '48.0.1', '48.0.2']}, ['release'], search_date=['>=2016-09-09', '<2016-09-10'])
        search.wait()
        self.assertEqual(data['release']['hang | ntdll.dll@0x6e1bc'], getnumbers(-1, -1, 6))
        self.assertEqual(data['release']['RtlpLowFragHeapFree | RtlFreeHeap | HeapFree | operator delete'], getnumbers(53, 36, -1))

    @responses.activate
    def test_get_signatures(self):
        s = statusflags.get_signatures(100, 'Firefox', {'release': ['48.0', '48.0.1', '48.0.2']}, ['release'], ['>=2016-09-09', '<2016-09-10'], ['hang | ntdll.dll@0x6e1bc', 'RtlpLowFragHeapFree | RtlFreeHeap | HeapFree | operator delete'], [], False)
        self.assertEqual(s['hang | ntdll.dll@0x6e1bc'], {'affected_channels': [('release', 171)],
                                                         'bugs': None,
                                                         'platforms': ['Windows'],
                                                         'selected_bug': None})
        self.assertEqual(s['RtlpLowFragHeapFree | RtlFreeHeap | HeapFree | operator delete'], {'affected_channels': [('release', 153)],
                                                                                               'bugs': None,
                                                                                               'platforms': ['Windows'],
                                                                                               'selected_bug': None})
        s = statusflags.get_signatures(100, 'Firefox', {'release': ['48.0', '48.0.1', '48.0.2']}, ['release'], ['>=2016-09-09', '<2016-09-10'], [], ['792226'], False)
        self.assertEqual(s['js::GCMarker::processMarkStackTop'], {'affected_channels': [('release', 1009)],
                                                                  'bugs': None,
                                                                  'platforms': ['Windows', 'Mac OS X'],
                                                                  'selected_bug': None})

    @responses.activate
    def test_reduce_set_of_bugs(self):
        signatures = ['js::GCMarker::processMarkStackTop', 'OOM | small']
        bugs_by_signature = socorro.Bugs.get_bugs(signatures)
        statusflags.reduce_set_of_bugs(bugs_by_signature)

        # bug 730283 is a dup of 719114 for signature js::GCMarker::processMarkStackTop
        self.assertEqual(set(bugs_by_signature[signatures[0]]), {792226, 789892, 719114, 1257309, 941491, 745334, 772441, 952381})

        self.assertEqual(set(bugs_by_signature[signatures[1]]), {1127554, 1153515, 683271, 1205771, 1034254, 1089682, 1115929, 1048619, 1060268, 1174324, 1066036, 1260730, 1081790, 1209673, 1057869, 1215181, 1045588, 1221974, 1059563, 1053934, 1224815, 1028720, 1205110, 1252090, 1177086})

    @responses.activate
    def test_get_stats_for_past_weeks(self):
        signature = 'js::TenuringTracer::moveObjectToTenured'
        analysis = {signature: {'firefox': True}}
        end_date = '2016-09-14'
        channel = ['release', 'beta', 'aurora', 'nightly', 'esr']
        start_date, min_date, versions_by_channel, start_date_by_channel, base_versions = statusflags.get_versions_info('Firefox')

        trends = statusflags.get_stats_for_past_weeks('Firefox', channel, start_date_by_channel, versions_by_channel, analysis, '', end_date)
        trends = trends[signature]

        self.assertEqual(trends['release'], {0: 6, 1: 8, 2: 7, 3: 6, 4: 4, 5: 4, 6: 1, 7: 0})
        self.assertEqual(trends['nightly'], {0: 8, 1: 15, 2: 13, 3: 13, 4: 29, 5: 52, 6: 4})
        self.assertEqual(trends['beta'], {0: 57, 1: 122, 2: 177, 3: 128, 4: 131, 5: 127, 6: 40})
        self.assertEqual(trends['aurora'], {0: 15, 1: 0, 2: 0, 3: 1, 4: 1, 5: 1, 6: 0})
        self.assertEqual(trends['esr'], {0: 0, 1: 0, 2: 1, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0, 10: 0, 11: 1, 12: 0, 13: 0, 14: 0, 15: 0})

    @responses.activate
    def test_get_partial(self):
        channel = ['release', 'beta', 'aurora', 'nightly', 'esr']
        signature = 'js::GCMarker::processMarkStackTop'
        bugids = socorro.Bugs.get_bugs([signature])

        self.assertEqual(set(bugids[signature]), {792226, 789892, 719114, 730283, 1257309, 941491, 745334, 772441, 952381})

        start_date, min_date, versions_by_channel, start_date_by_channel, base_versions = statusflags.get_versions_info('Firefox')
        search_date = statusflags.get_search_date('', start_date)
        sgninfo = statusflags.get_signatures(100, 'Firefox', versions_by_channel, channel, search_date, [signature], [], False)
        status_flags = Bugzilla.get_status_flags(base_versions=base_versions)
        bugs_history_info = statusflags.get_bugs_info(bugids[signature], status_flags)
        last_bugs_info, _ = statusflags.get_last_bugs_info(bugids[signature], signature, sgninfo, [], bugs_history_info, min_date)

        self.assertEqual(last_bugs_info['resolved-fixed-patched'], ['', utils.get_guttenberg_death()])
        self.assertEqual(last_bugs_info['resolved-fixed-unpatched'], ['', utils.get_guttenberg_death()])
        self.assertEqual(last_bugs_info['resolved-unfixed'], ['952381', utils.get_date_ymd('2014-05-13 12:12:41')])
        self.assertEqual(last_bugs_info['unresolved-assigned'], ['', utils.get_guttenberg_death()])
        self.assertEqual(last_bugs_info['unresolved-unassigned'], ['719114', utils.get_date_ymd('2016-08-30 23:15:17')])

        last_bug = statusflags.get_last_bug(bugids[signature], signature, sgninfo, [], bugs_history_info, min_date)
        self.assertEqual(last_bug, '719114')

    @responses.activate
    def test_get(self):
        info = statusflags.get('Firefox', 2, end_date='2016-09-14')

        self.assertEqual(info['base_versions']['aurora'], 50)
        self.assertEqual(info['base_versions']['beta'], 49)
        self.assertEqual(info['base_versions']['esr'], 45)
        self.assertEqual(info['base_versions']['nightly'], 51)
        self.assertEqual(info['base_versions']['release'], 48)

        self.assertEqual(info['start_dates']['aurora'], utils.get_date_ymd('2016-08-01'))
        self.assertEqual(info['start_dates']['beta'], utils.get_date_ymd('2016-08-02'))
        self.assertEqual(info['start_dates']['esr'], utils.get_date_ymd('2016-06-01'))
        self.assertEqual(info['start_dates']['nightly'], utils.get_date_ymd('2016-08-01'))
        self.assertEqual(info['start_dates']['release'], utils.get_date_ymd('2016-07-25'))

        self.assertTrue('IPCError-browser | ShutDownKill' in info['signatures'])

        isgn = info['signatures']['IPCError-browser | ShutDownKill']

        self.assertEqual(set(isgn['affected']), {('aurora', 117121), ('nightly', 66787), ('beta', 33327), ('release', 953), ('esr', 35)})
        self.assertEqual(isgn['bugid'], 1216774)
        self.assertEqual(set(isgn['bugs']), {1238657, 1151237, 1216774, 1260551, 1177484, 1173134, 1168272, 1132053, 1133597, 1167902, 1200671, 1213092, 1200646, 1213096, 1223594, 1200685, 1279293, 1206729, 1177425, 1219672, 1205467, 1240542, 1286053, 1266275, 1290280, 1259125, 1164155, 1150846})
        self.assertTrue(isgn['firefox'])
        self.assertEqual(isgn['leftovers'], [])
        self.assertEqual(set(isgn['platforms']), {'Windows', 'Mac OS X'})
        self.assertFalse(isgn['private'])

        def getnumbers(b, c, p):
            return {'browser': b, 'content': c, 'plugin': p}

        self.assertEqual(isgn['rank']['aurora'], getnumbers(-1, 1, -1))
        self.assertEqual(isgn['rank']['beta'], getnumbers(-1, 2, -1))
        self.assertEqual(isgn['rank']['esr'], getnumbers(-1, 1, -1))
        self.assertEqual(isgn['rank']['nightly'], getnumbers(-1, 1, -1))
        self.assertEqual(isgn['rank']['release'], getnumbers(-1, 20, -1))

        self.assertTrue(isgn['resolved'])

        self.assertEqual(isgn['trend']['aurora'], [8821, 18706, 21015, 20699, 22058, 20100, 5721])
        self.assertEqual(isgn['trend']['beta'], [325, 784, 817, 987, 1419, 18147, 10848])
        self.assertEqual(isgn['trend']['esr'], [4, 5, 2, 5, 2, 2, 3, 2, 0, 0, 5, 2, 1, 1, 2, 0])
        self.assertEqual(isgn['trend']['nightly'], [4961, 10192, 10261, 10294, 10631, 11974, 8471])
        self.assertEqual(isgn['trend']['release'], [158, 231, 169, 134, 117, 92, 49, 1])

        data = statusflags.generate_bug_report('IPCError-browser | ShutDownKill', isgn, info['status_flags'], info['base_versions'], info['start_dates'], end_date='2016-09-14')

        self.assertEqual(data['cf_status_firefox49'], 'affected')
        self.assertEqual(data['cf_status_firefox48'], 'affected')
        self.assertEqual(data['cf_status_firefox_esr45'], 'affected')
        self.assertEqual(data['cf_status_firefox50'], 'affected')
        self.assertEqual(data['cf_status_firefox51'], 'affected')

        self.assertEqual(data['comment']['body'], 'Crash volume for signature \'IPCError-browser | ShutDownKill\':\n - nightly (version 51): 66787 crashes from 2016-08-01 00:00:00+00:00.\n - aurora  (version 50): 117121 crashes from 2016-08-01 00:00:00+00:00.\n - beta    (version 49): 33327 crashes from 2016-08-02 00:00:00+00:00.\n - release (version 48): 953 crashes from 2016-07-25 00:00:00+00:00.\n - esr     (version 45): 35 crashes from 2016-06-01 00:00:00+00:00.\n\nCrash volume on the last weeks (Week N is from 09-12 to 09-18):\n            W. N-1  W. N-2  W. N-3  W. N-4  W. N-5  W. N-6\n - nightly   10192   10261   10294   10631   11974    8471\n - aurora    18706   21015   20699   22058   20100    5721\n - beta        784     817     987    1419   18147   10848\n - release     231     169     134     117      92      49\n - esr           5       2       5       2       2       3\n\nAffected platforms: Windows, Mac OS X\n\nCrash rank on the last 7 days:\n             Browser Content     Plugin\n - nightly           #1\n - aurora            #1\n - beta              #2\n - release           #20\n - esr               #1')


if __name__ == '__main__':
    unittest.main()
