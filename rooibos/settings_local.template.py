DEBUG = True
TEMPLATE_DEBUG = DEBUG
#LOGGING_OUTPUT_ENABLED = True

# Needed to enable compression JS and CSS files
COMPRESS = True
MEDIA_URL = '/static/'
MEDIA_ROOT = 'd:/mdid/rooibos/static/'


ADMINS = (
#    ('Your name', 'your@email.example'),
)

MANAGERS = ADMINS

# Settings for MySQL
DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_OPTIONS = {
    'use_unicode': True,
    'charset': 'utf8',
}

# Settings for Microsoft SQL Server
#DATABASE_ENGINE = 'sql_server.pyodbc'
#DATABASE_OPTIONS= {
#    'driver': 'SQL Native Client',
#    'MARS_Connection': True,
#}

# Settings for all database systems
DATABASE_NAME = 'rooibos'             # Or path to database file if using sqlite3.
DATABASE_USER = 'rooibos'             # Not used with sqlite3.
DATABASE_PASSWORD = 'rooibos'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

DEFAULT_CHARSET = 'utf-8'
DATABASE_CHARSET = 'utf8'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'e#!poDuIJ}N,".K=H:T/4z5POb;Gl/N6$6a&,(DRAHUF5c",_p'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

SOLR_URL = 'http://127.0.0.1:8983/solr/'

SCRATCH_DIR = 'c:/mdid-scratch/'
AUTO_STORAGE_DIR = 'c:/mdid-collections/'

# Legacy setting for ImageViewer 2 support
SECURE_LOGIN = False


LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/'

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

INTERNAL_IPS = ('127.0.0.1',)

HELP_URL = 'http://mdid.org/help/'

DEFAULT_LANGUAGE = 'en-us'

GOOGLE_ANALYTICS_MODEL = True

FLICKR_KEY = ''
FLICKR_SECRET = ''

# Set to None if you don't subscribe to ARTstor
ARTSTOR_GATEWAY = None
#ARTSTOR_GATEWAY = 'http://sru.artstor.org/SRU/artstor.htm'

OPEN_OFFICE_PATH = 'C:/Program Files/OpenOffice.org 3/program/'

GEARMAN_SERVERS = ['127.0.0.1']

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'rooibos.auth.ldapauth.LdapAuthenticationBackend',
#    'rooibos.auth.mailauth.ImapAuthenticationBackend',
#    'rooibos.auth.mailauth.PopAuthenticationBackend',
)

MIDDLEWARE_CLASSES = (
    'rooibos.auth.middleware.BasicAuthenticationMiddleware',
)

LDAP_AUTH = (
    {
        'uri': 'ldap://ldap.example.edu',
        'base': 'ou=People,o=example',
        'cn': 'cn',
        'version': 2,
        'scope': 1,
        'options': {'OPT_X_TLS_TRY': 1},
        'attributes': ('sn', 'mail', 'givenName', 'eduPersonPrimaryAffiliation'),
        'firstname': 'givenname',
        'lastname': 'sn',
        'email': 'mail',
    },
)

IMAP_AUTH = (
    {
        'server': 'imap.example.edu',
        'port': 993,
        'domain': 'example.edu',
        'secure': True,
    },
)

POP_AUTH = (
    {
        'server': 'pop.gmail.com',
        'port': 995,
        'domain': 'gmail.com',
        'secure': True,
    },
)

SESSION_COOKIE_AGE = 6 * 3600  # in seconds

SSL_PORT = None  # ':443'

# Theme colors for use in CSS
PRIMARY_COLOR = "rgb(152, 189, 198)"
SECONDARY_COLOR = "rgb(118, 147, 154)"

WWW_AUTHENTICATION_REALM = "Please log in to access media from MDID at Your University"

CUSTOM_TRACKER_HTML = ""

EXPOSE_TO_CONTEXT = ('STATIC_DIR', 'PRIMARY_COLOR', 'SECONDARY_COLOR', 'CUSTOM_TRACKER_HTML', 'ADMINS')

# The Megazine viewer is using a third party component that has commercial
# licensing requirements.  Before enabling the component here please make
# sure you are not violating the agreements listed in static/megazine/COPYING.
MEGAZINE_VIEWER = False

# To use a commercial licensed flowplayer, enter your flowplayer key here
# and add the flowplayer.commercial-3.x.x.swf file to the
# rooibos/static/flowplayer directory
FLOWPLAYER_KEY = ""

additional_settings = [
#    'apps.jmutube.settings_local',
#    'apps.svohp.settings_local',
]
