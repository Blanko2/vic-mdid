DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
#    ('Your name', 'your@email.example'),
)

MANAGERS = ADMINS

#DATABASE_ENGINE = 'sqlite3'
DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_OPTIONS = {
    'use_unicode': True,
    'charset': 'utf8',
}

DATABASE_NAME = 'rooibos'             # Or path to database file if using sqlite3.
DATABASE_USER = 'rooibos'             # Not used with sqlite3.
DATABASE_PASSWORD = 'rooibos'         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

DEFAULT_CHARSET = 'utf-8'
DATABASE_CHARSET =  'utf8'

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

TEMPLATE_DIRS = (
    'd:/dev/rooibos/rooibos/templates',
)

SOLR_URL = 'http://127.0.0.1:8983/solr/'

SCRATCH_DIR = 'd:/dev/rooibos/scratch/'

# Legacy setting for ImageViewer 2 support
SECURE_LOGIN = False


LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

INTERNAL_IPS = ('127.0.0.1',)

HELP_URL = 'https://wiki.cit.jmu.edu/mdidhelp/index.php/Help_v1:'

DEFAULT_LANGUAGE = 'en-us'

GOOGLE_ANALYTICS_MODEL = True

FLICKR_KEY = ''
FLICKR_SECRET = ''

# Set to None if you don't subscribe to ARTstor
ARTSTOR_GATEWAY = None
#ARTSTOR_GATEWAY = 'http://sru.artstor.org/SRU/artstor.htm'

STATIC_DIR = 'd:/dev/rooibos/rooibos/static/'
OPEN_OFFICE_PATH = 'C:/Program Files/OpenOffice.org 3/program/'

GEARMAN_SERVERS = ['127.0.0.1']

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
#    'jmutube.jmu_authentication.Jmu_Authentication_Backend',
)

# six hour session timeout
SESSION_COOKIE_AGE = 6 * 3600

#SSL_PORT = ':443'
SSL_PORT = None

ADDITIONAL_SETTINGS = [
#    'apps.jmutube.settings_local',
]
