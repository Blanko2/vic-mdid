from django.conf import settings
import urlparse

__version__ = '$Id: mediawiki_family.py 5751 2008-07-24 16:47:58Z nicdumz $'

import family

# Based on the MediaWiki family
# user-config.py: usernames['rooibos']['rooibos'] = 'User name'

def parse_help_url(url):
    (scheme, netloc, path, params, query, fragment) = urlparse.urlparse(url)
    if path.endswith(':'):
        (path, namespace) = path[:-1].rsplit('/', 1)
    else:
        namespace = ''
    if path.endswith('/index.php'):
        path = path[:-10]
    return (scheme, netloc, path, namespace)


class Family(family.Family):
    def __init__(self):
        
        (scheme, netloc, path, namespace) = parse_help_url(settings.HELP_URL)
        self.help_scheme = scheme
        self.help_path = path
        self.help_namespace = namespace
        
        family.Family.__init__(self)
        self.name = 'rooibos'

        self.langs = {
            'rooibos': netloc,
        }

        self.namespaces[100] = {
            '_default': u'Help v1',
        }
        self.namespaces[101] = {
            '_default': u'Help v1 talk',
        }

    def version(self, code):
        return '1.13.1'

    def protocol(self, code):
        """
        Can be overridden to return 'https'. Other protocols are not supported.
        """
        return self.help_scheme

    def scriptpath(self, code):
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        """
        return self.help_path
