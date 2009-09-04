# -*- coding: utf-8  -*-

__version__ = '$Id: incubator_family.py 7200 2009-09-03 09:27:00Z alexsh $'

import family

# The Wikimedia Incubator family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'incubator'
        self.langs = {
            'incubator': 'incubator.wikimedia.org',
        }
        if family.config.SSL_connection:
            self.langs['incubator'] = None

        self.namespaces[4] = {
            '_default': [u'Incubator', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Incubator talk', self.namespaces[5]['_default']],
        }
        self.namespaces[100] = {
            '_default': u'Lost',
        }
        self.namespaces[101] = {
            '_default': u'Lost talk',
        }

    def version(self, code):
        return '1.16alpha-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    if family.config.SSL_connection:
        def hostname(self, code):
            return 'secure.wikimedia.org'

        def protocol(self, code):
            return 'https'

        def scriptpath(self, code):
            return '/wikipedia/incubator/w'

        def nicepath(self, code):
            return '/wikipedia/incubator/wiki/'

