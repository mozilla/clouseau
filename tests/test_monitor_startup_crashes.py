# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import libmozdata.socorro as socorro
import responses
from tests.auto_mock import MockTestCase
from clouseau import monitor_startup_crashes as msc


class MonitorStartupCrashesTest(MockTestCase):
    mock_urls = [
        socorro.Socorro.CRASH_STATS_URL,
        'https://crash-analysis.mozilla.com/rkaiser'
    ]

    @responses.activate
    def test_monitor(self):
        data = msc.get_crashanalysis_data()
        data = msc.convert(data)

        mail = msc.monitor(date='2016-08-11', data=data, verbose=False)
        self.assertIsNotNone(mail)
        self.assertEquals(mail['title'], 'Spikes in nightly')
        self.assertEquals(mail['body'], "Hi all,\n\nWe\'ve one or more spike in startup crashes.\nHere the results:\n\n== Firefox ==\n  nightly:\n   - Top 3 of startup crashers the 2016-08-10:\n    * IPCError-browser | ShutDownKill: 956\n    * F1398665248_____________________________: 208\n    * mozalloc_abort | NS_DebugBreak | mozilla::ipc::FatalError | mozilla::net::PNeckoChild::SendPHttpChannelConstructor: 39\n\n   https://crash-stats.mozilla.com/search/?date=%3E%3D2016-08-11&date=%3C2016-08-12&product=Firefox&version=51.0a1&release_channel=nightly&uptime=%3C60\n\n   - Top 3 of startup crashers the 2016-08-11:\n    * nsIChannel::GetLoadInfo: 1641\n    * IPCError-browser | ShutDownKill: 848\n    * F1398665248_____________________________: 253\n\n   https://crash-stats.mozilla.com/search/?date=%3E%3D2016-08-11&date=%3C2016-08-12&product=Firefox&version=51.0a1&release_channel=nightly&uptime=%3C60\n\n== FennecAndroid ==\n  nightly:\n   - Top 3 of startup crashers the 2016-08-10:\n    * java.lang.IllegalArgumentException: ViewStub must have a valid layoutResource at android.view.ViewStub.inflate(ViewStub.java): 8\n    * java.lang.IndexOutOfBoundsException: at java.util.LinkedList.get(LinkedList.java): 4\n    * java.lang.NullPointerException: Attempt to get length of null array at org.mozilla.gecko.telemetry.stores.TelemetryJSONFilePingStore.maybePrunePings(TelemetryJSONFilePingStore.java): 2\n\n   https://crash-stats.mozilla.com/search/?date=%3E%3D2016-08-11&date=%3C2016-08-12&product=FennecAndroid&version=51.0a1&release_channel=nightly&uptime=%3C60\n\n   - Top 3 of startup crashers the 2016-08-11:\n    * nsPrefetchNode::OnStartRequest: 56\n    * java.lang.IndexOutOfBoundsException: at java.util.LinkedList.get(LinkedList.java): 4\n    * java.lang.NoClassDefFoundError: android.support.v7.internal.view.menu.MenuBuilder at android.support.v7.app.AppCompatDelegateImplV7.preparePanel(Unknown Source): 3\n\n   https://crash-stats.mozilla.com/search/?date=%3E%3D2016-08-11&date=%3C2016-08-12&product=FennecAndroid&version=51.0a1&release_channel=nightly&uptime=%3C60\n\n\n\nSincerely,\nRelease Management Bot")

        mail = msc.monitor(date='2016-07-31', data=data, verbose=False)
        self.assertIsNotNone(mail)
        self.assertEquals(mail['title'], 'Spikes in aurora')
        self.assertEquals(mail['body'], "Hi all,\n\nWe\'ve one or more spike in startup crashes.\nHere the results:\n\n== Firefox ==\n  aurora:\n   - Top 3 of startup crashers the 2016-07-30:\n    * F1398665248_____________________________: 492\n    * IPCError-browser | ShutDownKill: 239\n    * Abort | JS_InitWithFailureDiagnostic: u_init() failed | mozalloc_abort | NS_DebugBreak | NS_InitXPCOM2: 173\n\n   https://crash-stats.mozilla.com/search/?date=%3E%3D2016-07-31&date=%3C2016-08-01&product=Firefox&version=49.0a2&release_channel=aurora&uptime=%3C60\n\n   - Top 3 of startup crashers the 2016-07-31:\n    * F1398665248_____________________________: 7515\n    * IPCError-browser | ShutDownKill: 194\n    * Abort | JS_InitWithFailureDiagnostic: u_init() failed | mozalloc_abort | NS_DebugBreak | NS_InitXPCOM2: 88\n\n   https://crash-stats.mozilla.com/search/?date=%3E%3D2016-07-31&date=%3C2016-08-01&product=Firefox&version=49.0a2&release_channel=aurora&uptime=%3C60\n\n\n\nSincerely,\nRelease Management Bot")

        mail = msc.monitor(date='2016-09-01', data=data, verbose=False)
        self.assertIsNone(mail)

if __name__ == '__main__':
    unittest.main()
