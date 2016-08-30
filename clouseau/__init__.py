import os
import libmozdata.config as config


here = os.path.abspath(__file__)
path = os.path.join(here, '../config.ini')
path = os.path.abspath(path)
config.set_config(config.ConfigIni(path))
