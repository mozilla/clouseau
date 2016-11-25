# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest
import tempfile
import shutil
from libmozdata.hgmozilla import Mercurial
import libmozdata.socorro as socorro
import responses
from tests.auto_mock import MockTestCase
from clouseau import guiltypatches


class GuiltyPatchesTest(MockTestCase):
    mock_urls = [
        socorro.Socorro.CRASH_STATS_URL,
        Mercurial.HG_URL
    ]

    def tearDown(self):
        shutil.rmtree(self.tmpdst)
        super(GuiltyPatchesTest, self).tearDown()

    def setUp(self):
        self.tmpdst = tempfile.mkdtemp()
        super(GuiltyPatchesTest, self).setUp()

    @responses.activate
    def test_generate(self):
        guiltypatches.generate(channel='nightly', product='FennecAndroid', date='2016-08-15', threshold=1, output_dir=self.tmpdst, verbose=False)
        dates = guiltypatches.getdates(self.tmpdst)
        self.assertEqual(dates, ['2016-08-15'])
        data = guiltypatches.get('nightly', 'FennecAndroid', dates[0], self.tmpdst)
        self.assertEqual(data, {'jemalloc_crash | arena_dalloc | nsTArray_base<T>::ShrinkCapacity | nsTArray_Impl<T>::RemoveElementsAt | nsUrlClassifierPrefixSet::MakePrefixSet': [{'bt': [['jemalloc_crash', {'node': '6e191a55c3d2', 'line': 1625, 'patches': [], 'filename': 'memory/mozjemalloc/jemalloc.c'}], ['arena_dalloc', {'node': '6e191a55c3d2', 'line': 1625, 'patches': [], 'filename': 'memory/mozjemalloc/jemalloc.c'}], ['nsTArray_base<nsTArrayFallibleAllocator, nsTArray_CopyWithMemutils>::ShrinkCapacity', {'patches': [], 'filename': ''}], ['nsTArray_Impl<nsTArray<short unsigned int>, nsTArrayInfallibleAllocator>::RemoveElementsAt', {'node': '6e191a55c3d2', 'line': 1899, 'patches': [{'node': '2c42c82251d63cd38a0a59c3f1ed82d4019ec7a1', 'pushdate': '2016-08-12 16:45:27+00:00'}], 'filename': 'xpcom/glue/nsTArray.h'}], ['nsUrlClassifierPrefixSet::MakePrefixSet', {'node': '6e191a55c3d2', 'line': 105, 'patches': [], 'filename': 'toolkit/components/url-classifier/nsUrlClassifierPrefixSet.cpp'}], ['nsUrlClassifierPrefixSet::SetPrefixes', {'node': '6e191a55c3d2', 'line': 105, 'patches': [], 'filename': 'toolkit/components/url-classifier/nsUrlClassifierPrefixSet.cpp'}], ['mozilla::safebrowsing::LookupCache::ConstructPrefixSet', {'node': '6e191a55c3d2', 'line': 582, 'patches': [], 'filename': 'toolkit/components/url-classifier/LookupCache.cpp'}], ['mozilla::safebrowsing::LookupCache::Build', {'node': '6e191a55c3d2', 'line': 582, 'patches': [], 'filename': 'toolkit/components/url-classifier/LookupCache.cpp'}], ['mozilla::safebrowsing::Classifier::ApplyTableUpdates', {'node': '6e191a55c3d2', 'line': 664, 'patches': [], 'filename': 'toolkit/components/url-classifier/Classifier.cpp'}], ['mozilla::safebrowsing::Classifier::ApplyUpdates', {'node': '6e191a55c3d2', 'line': 664, 'patches': [], 'filename': 'toolkit/components/url-classifier/Classifier.cpp'}], ['nsUrlClassifierDBServiceWorker::FinishUpdate', {'node': '6e191a55c3d2', 'line': 579, 'patches': [], 'filename': 'toolkit/components/url-classifier/nsUrlClassifierDBService.cpp'}], ['mozilla::detail::RunnableMethodImpl<nsresult (nsIUrlClassifierDBService::*)(), true, false>::Run', {'node': '6e191a55c3d2', 'line': 729, 'patches': [], 'filename': 'xpcom/glue/nsThreadUtils.h'}], ['nsThread::ProcessNextEvent', {'node': '6e191a55c3d2', 'line': 1058, 'patches': [], 'filename': 'xpcom/threads/nsThread.cpp'}], ['NS_ProcessNextEvent', {'node': '6e191a55c3d2', 'line': 290, 'patches': [], 'filename': 'xpcom/glue/nsThreadUtils.cpp'}], ['mozilla::ipc::MessagePumpForNonMainThreads::Run', {'node': '6e191a55c3d2', 'line': 368, 'patches': [], 'filename': 'ipc/glue/MessagePump.cpp'}], ['MessageLoop::Run', {'node': '6e191a55c3d2', 'line': 225, 'patches': [], 'filename': 'ipc/chromium/src/base/message_loop.cc'}], ['nsThread::ThreadFunc', {'node': '6e191a55c3d2', 'line': 1058, 'patches': [], 'filename': 'xpcom/threads/nsThread.cpp'}], ['_pt_root', {'node': 'fe895421dfbe', 'line': 216, 'patches': [], 'filename': 'nsprpub/pr/src/pthreads/ptthread.c'}]], 'count': 1, 'uuids': ['3ac31c5c-aeff-495b-a5ec-076c62160817']}], 'mozilla::safebrowsing::HashStore::ApplyUpdate': [{'bt': [['mozilla::safebrowsing::HashStore::ApplyUpdate', {'node': '6e191a55c3d2', 'line': 515, 'patches': [{'node': '2c42c82251d63cd38a0a59c3f1ed82d4019ec7a1', 'pushdate': '2016-08-12 16:45:27+00:00'}], 'filename': 'xpcom/glue/nsTArray.h'}], ['mozilla::safebrowsing::Classifier::ApplyTableUpdates', {'node': '6e191a55c3d2', 'line': 611, 'patches': [], 'filename': 'toolkit/components/url-classifier/Classifier.cpp'}], ['mozilla::safebrowsing::Classifier::ApplyUpdates', {'node': '6e191a55c3d2', 'line': 611, 'patches': [], 'filename': 'toolkit/components/url-classifier/Classifier.cpp'}], ['nsUrlClassifierDBServiceWorker::FinishUpdate', {'node': '6e191a55c3d2', 'line': 579, 'patches': [], 'filename': 'toolkit/components/url-classifier/nsUrlClassifierDBService.cpp'}], ['mozilla::detail::RunnableMethodImpl<nsresult (nsIUrlClassifierDBService::*)(), true, false>::Run', {'node': '6e191a55c3d2', 'line': 729, 'patches': [], 'filename': 'xpcom/glue/nsThreadUtils.h'}], ['nsThread::ProcessNextEvent', {'node': '6e191a55c3d2', 'line': 1058, 'patches': [], 'filename': 'xpcom/threads/nsThread.cpp'}], ['NS_ProcessNextEvent', {'node': '6e191a55c3d2', 'line': 290, 'patches': [], 'filename': 'xpcom/glue/nsThreadUtils.cpp'}], ['mozilla::ipc::MessagePumpForNonMainThreads::Run', {'node': '6e191a55c3d2', 'line': 338, 'patches': [], 'filename': 'ipc/glue/MessagePump.cpp'}], ['MessageLoop::Run', {'node': '6e191a55c3d2', 'line': 225, 'patches': [], 'filename': 'ipc/chromium/src/base/message_loop.cc'}], ['nsThread::ThreadFunc', {'node': '6e191a55c3d2', 'line': 1058, 'patches': [], 'filename': 'xpcom/threads/nsThread.cpp'}], ['_pt_root', {'node': '97a52326b06a', 'line': 216, 'patches': [], 'filename': 'nsprpub/pr/src/pthreads/ptthread.c'}]], 'count': 1, 'uuids': ['b21495b6-121b-4073-a06a-4059e2160818']}], 'nsUrlClassifierPrefixSet::MakePrefixSet': [{'bt': [['nsUrlClassifierPrefixSet::MakePrefixSet', {'node': '6e191a55c3d2', 'line': 2028, 'patches': [{'node': '2c42c82251d63cd38a0a59c3f1ed82d4019ec7a1', 'pushdate': '2016-08-12 16:45:27+00:00'}], 'filename': 'xpcom/glue/nsTArray.h'}], ['nsUrlClassifierPrefixSet::SetPrefixes', {'node': '6e191a55c3d2', 'line': 83, 'patches': [], 'filename': 'toolkit/components/url-classifier/nsUrlClassifierPrefixSet.cpp'}], ['mozilla::safebrowsing::LookupCache::ConstructPrefixSet', {'node': '6e191a55c3d2', 'line': 582, 'patches': [], 'filename': 'toolkit/components/url-classifier/LookupCache.cpp'}], ['mozilla::safebrowsing::LookupCache::Build', {'node': '6e191a55c3d2', 'line': 582, 'patches': [], 'filename': 'toolkit/components/url-classifier/LookupCache.cpp'}], ['mozilla::safebrowsing::Classifier::ApplyTableUpdates', {'node': '6e191a55c3d2', 'line': 664, 'patches': [], 'filename': 'toolkit/components/url-classifier/Classifier.cpp'}], ['mozilla::safebrowsing::Classifier::ApplyUpdates', {'node': '6e191a55c3d2', 'line': 664, 'patches': [], 'filename': 'toolkit/components/url-classifier/Classifier.cpp'}], ['nsUrlClassifierDBServiceWorker::FinishUpdate', {'node': '6e191a55c3d2', 'line': 579, 'patches': [], 'filename': 'toolkit/components/url-classifier/nsUrlClassifierDBService.cpp'}], ['mozilla::detail::RunnableMethodImpl<nsresult (nsIUrlClassifierDBService::*)(), true, false>::Run', {'node': '6e191a55c3d2', 'line': 729, 'patches': [], 'filename': 'xpcom/glue/nsThreadUtils.h'}], ['nsThread::ProcessNextEvent', {'node': '6e191a55c3d2', 'line': 1058, 'patches': [], 'filename': 'xpcom/threads/nsThread.cpp'}], ['NS_ProcessNextEvent', {'node': '6e191a55c3d2', 'line': 290, 'patches': [], 'filename': 'xpcom/glue/nsThreadUtils.cpp'}], ['mozilla::ipc::MessagePumpForNonMainThreads::Run', {'node': '6e191a55c3d2', 'line': 368, 'patches': [], 'filename': 'ipc/glue/MessagePump.cpp'}], ['MessageLoop::Run', {'node': '6e191a55c3d2', 'line': 225, 'patches': [], 'filename': 'ipc/chromium/src/base/message_loop.cc'}], ['nsThread::ThreadFunc', {'node': '6e191a55c3d2', 'line': 1058, 'patches': [], 'filename': 'xpcom/threads/nsThread.cpp'}], ['_pt_root', {'node': '054d4856cea6', 'line': 216, 'patches': [], 'filename': 'nsprpub/pr/src/pthreads/ptthread.c'}]], 'count': 1, 'uuids': ['01efd790-1f0e-4865-b5fe-249b62160816']}]})


if __name__ == '__main__':
    unittest.main()