# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import libmozdata.socorro as socorro
import libmozdata.bugzilla as bugzilla
import responses
from tests.auto_mock import MockTestCase
from clouseau import monitor_startup_crashes as msc


class MonitorStartupCrashesTest(MockTestCase):
    mock_urls = [
        socorro.Socorro.CRASH_STATS_URL,
        bugzilla.Bugzilla.URL,
        'https://crash-analysis.mozilla.com'
    ]

    @responses.activate
    def test_monitor(self):
        data = msc.get_crashanalysis_data()
        data = msc.convert(data)
        mail = msc.monitor(date='2016-08-11', data=data, verbose=False)
        self.assertIsNotNone(mail)
        self.assertEqual(mail['title'], 'Spikes in startup crashes in nightly')
        self.assertEqual(mail['body'], '<!doctype html>\n<html lang="en-us">\n<head>\n  <meta charset="utf-8">\n  <title>Spikes</title>\n</head>\n<body>\n<p>Hi all,</p>\n<p>We\'ve two spikes in startup crashes.<br>\n<ul style="padding: 0">\n<li>FennecAndroid\n<ul>\n<li>nightly (<b>125</b> crashes reported):<br>\nMost significant increases from 2016-08-10 to 2016-08-11 (<a href="https://crash-stats.mozilla.com/search/?date=%3E%3D2016-08-11&date=%3C2016-08-12&product=FennecAndroid&release_channel=nightly&uptime=%3C60&version=51.0a1">top startup crashers from Socorro</a>):\n<ul>\n<li>nsPrefetchNode::OnStartRequest: <b>increased from 0 to 56 (+inf%)</b>.\n<ul>\n<li><a href="https://bugzil.la/1294159">Bug 1294159</a></li>\n</ul>\n</li>\n<li>java.lang.NoClassDefFoundError: android.support.v7.internal.view.menu.MenuBuilder at android.support.v7.app.AppCompatDelegateImplV7.preparePanel(Unknown Source): <b>increased from 0 to 3 (+inf%)</b>.\n<ul>\n</ul>\n</li>\n</ul>\n</li>\n</ul>\n</li>\n<li>Firefox\n<ul>\n<li>nightly (<b>6306</b> crashes reported):<br>\nMost significant increases from 2016-08-10 to 2016-08-11 (<a href="https://crash-stats.mozilla.com/search/?date=%3E%3D2016-08-11&date=%3C2016-08-12&product=Firefox&release_channel=nightly&uptime=%3C60&version=51.0a1">top startup crashers from Socorro</a>):\n<ul>\n<li>nsIChannel::GetLoadInfo: <b>increased from 0 to 1641 (+inf%)</b>.\n<ul>\n<li><a href="https://bugzil.la/1294159">Bug 1294159</a></li>\n</ul>\n</li>\n<li>nsPrefetchNode::OnStartRequest: <b>increased from 0 to 84 (+inf%)</b>.\n<ul>\n<li><a href="https://bugzil.la/1294159">Bug 1294159</a></li>\n</ul>\n</li>\n<li>F1398665248_____________________________: <b>increased from 208 to 253 (+22%)</b>.\n<ul>\n<li><a href="https://bugzil.la/713138">Bug 713138</a></li>\n<li><a href="https://bugzil.la/763237">Bug 763237</a></li>\n<li><a href="https://bugzil.la/774281">Bug 774281</a></li>\n<li><a href="https://bugzil.la/782395">Bug 782395</a></li>\n<li><a href="https://bugzil.la/787014">Bug 787014</a></li>\n<li><a href="https://bugzil.la/790368">Bug 790368</a></li>\n<li><a href="https://bugzil.la/812047">Bug 812047</a></li>\n<li><a href="https://bugzil.la/814003">Bug 814003</a></li>\n<li><a href="https://bugzil.la/846126">Bug 846126</a></li>\n<li><a href="https://bugzil.la/858831">Bug 858831</a></li>\n<li><a href="https://bugzil.la/891813">Bug 891813</a></li>\n<li><a href="https://bugzil.la/1082670">Bug 1082670</a></li>\n<li><a href="https://bugzil.la/1120011">Bug 1120011</a></li>\n<li><a href="https://bugzil.la/1122646">Bug 1122646</a></li>\n<li><a href="https://bugzil.la/1155379">Bug 1155379</a></li>\n<li><a href="https://bugzil.la/1157078">Bug 1157078</a></li>\n<li><a href="https://bugzil.la/1158561">Bug 1158561</a></li>\n<li><a href="https://bugzil.la/1226960">Bug 1226960</a></li>\n<li><a href="https://bugzil.la/1228735">Bug 1228735</a></li>\n<li><a href="https://bugzil.la/1275682">Bug 1275682</a></li>\n<li><a href="https://bugzil.la/1330610">Bug 1330610</a></li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>\n</p>\n<p>Sincerely,<br>\nRelease Management Bot\n</p>\n</body>\n</html>')

        mail = msc.monitor(date='2016-07-31', data=data, verbose=False)
        self.assertIsNotNone(mail)
        self.assertEqual(mail['title'], 'Spikes in startup crashes in aurora')
        self.assertEqual(mail['body'], '<!doctype html>\n<html lang="en-us">\n<head>\n  <meta charset="utf-8">\n  <title>Spikes</title>\n</head>\n<body>\n<p>Hi all,</p>\n<p>We\'ve one spike in startup crashes.<br>\n<ul style="padding: 0">\n<li>Firefox\n<ul>\n<li>aurora (<b>10956</b> crashes reported):<br>\nMost significant increases from 2016-07-30 to 2016-07-31 (<a href="https://crash-stats.mozilla.com/search/?date=%3E%3D2016-07-31&date=%3C2016-08-01&product=Firefox&release_channel=aurora&uptime=%3C60&version=49.0a2">top startup crashers from Socorro</a>):\n<ul>\n<li>F1398665248_____________________________: <b>increased from 492 to 7515 (+1427%)</b>.\n<ul>\n<li><a href="https://bugzil.la/713138">Bug 713138</a></li>\n<li><a href="https://bugzil.la/763237">Bug 763237</a></li>\n<li><a href="https://bugzil.la/774281">Bug 774281</a></li>\n<li><a href="https://bugzil.la/782395">Bug 782395</a></li>\n<li><a href="https://bugzil.la/787014">Bug 787014</a></li>\n<li><a href="https://bugzil.la/790368">Bug 790368</a></li>\n<li><a href="https://bugzil.la/812047">Bug 812047</a></li>\n<li><a href="https://bugzil.la/814003">Bug 814003</a></li>\n<li><a href="https://bugzil.la/846126">Bug 846126</a></li>\n<li><a href="https://bugzil.la/858831">Bug 858831</a></li>\n<li><a href="https://bugzil.la/891813">Bug 891813</a></li>\n<li><a href="https://bugzil.la/1082670">Bug 1082670</a></li>\n<li><a href="https://bugzil.la/1120011">Bug 1120011</a></li>\n<li><a href="https://bugzil.la/1122646">Bug 1122646</a></li>\n<li><a href="https://bugzil.la/1155379">Bug 1155379</a></li>\n<li><a href="https://bugzil.la/1157078">Bug 1157078</a></li>\n<li><a href="https://bugzil.la/1158561">Bug 1158561</a></li>\n<li><a href="https://bugzil.la/1226960">Bug 1226960</a></li>\n<li><a href="https://bugzil.la/1228735">Bug 1228735</a></li>\n<li><a href="https://bugzil.la/1275682">Bug 1275682</a></li>\n<li><a href="https://bugzil.la/1330610">Bug 1330610</a></li>\n</ul>\n</li>\n<li>nss3.dll@0x1e9700 | GetFileInfo: <b>increased from 0 to 26 (+inf%)</b>.\n<ul>\n<li><a href="https://bugzil.la/1229252">Bug 1229252</a></li>\n</ul>\n</li>\n<li>webcamsplitterfilter.ax@0x19c4c5: <b>increased from 0 to 15 (+inf%)</b>.\n<ul>\n</ul>\n</li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>\n</p>\n<p>Sincerely,<br>\nRelease Management Bot\n</p>\n</body>\n</html>')

        mail = msc.monitor(date='2016-09-01', data=data, verbose=False)
        self.assertIsNone(mail)


if __name__ == '__main__':
    unittest.main()
