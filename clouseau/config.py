# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
from libmozdata import config


class ClouseauConfigIni(config.ConfigIni):

    def __init__(self, path=None):
        super(ClouseauConfigIni, self).__init__(path)

    def get_default_paths(self):
        return [os.path.join(os.getcwd(), 'clouseau.ini'), os.path.expanduser('~/.clouseau.ini')]


__config = ClouseauConfigIni()


def get(section, option, default=None, type=str):
    global __config
    return __config.get(section, option, default=default, type=type)
