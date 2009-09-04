# -*- coding: utf-8  -*-

__version__ = '$Id: supertux_family.py 5919 2008-09-26 12:28:58Z multichill $'

import family

# The project wiki of SuperTux, an open source arcade game.

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'supertux'
        self.langs = {
            'en': 'supertux.lethargik.org',
        }
        self.namespaces[4] = {
            '_default': [u'SuperTux', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'SuperTux talk', self.namespaces[5]['_default']],
        }

    def scriptpath(self, code):
        return '/wiki'

    def version(self, code):
        return "1.13.1"
