# DON'T PUT ANY LOCALIZED SETTINGS OR SECRETS IN THIS FILE
# they should go in settings_local.py instead
# with a blank setting in settings_local.template.py

import os.path

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
#    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
)

MIDDLEWARE_CLASSES = (
    'rooibos.sslredirect.SSLRedirect',
    'django.middleware.common.CommonMiddleware',
    'rooibos.util.stats_middleware.StatsMiddleware',
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'rooibos.api.middleware.CookielessSessionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
)

ROOT_URLCONF = 'rooibos.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django.contrib.comments',
    'django.contrib.redirects',
    'django_extensions',
    'google_analytics',
    'rooibos.data',
    'rooibos.migration',
    'rooibos.util',
    'rooibos.access',
    'rooibos.solr',
    'rooibos.storage',
    'rooibos.legacy',
    'rooibos.nasa',
    'rooibos.ui',
    'rooibos.viewers',
    'rooibos.help',
    'rooibos.presentation',
    'rooibos.statistics',
    'rooibos.flickr',
    'rooibos.converters',
    'rooibos.artstor',
    'rooibos.contrib.tagging',
    'rooibos.workers',
    'pagination',
    'impersonate',
)

STORAGE_SYSTEMS = {
    'local': 'rooibos.storage.localfs.LocalFileSystemStorageSystem',
    'online': 'rooibos.storage.online.OnlineStorageSystem',
    'streaming': 'rooibos.storage.streaming.StreamingStorageSystem',
}

GROUP_MANAGERS = {
    'nasaimageexchange': 'rooibos.nasa.nix.NasaImageExchange',
}

WEBSERVICE_NAMESPACE = "http://mdid.jmu.edu/webservices"

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)


additional_settings = [
    'settings_local',
]

# Load settings for additional applications
for settings in additional_settings:
    print "Loading additional settings from %s" % settings
    module = __import__(settings, globals(), locals(), 'rooibos')
    for setting in dir(module):
        if setting == setting.upper():
            if locals().has_key(setting):
                if isinstance(locals()[setting], dict):
                    locals()[setting].update(getattr(module, setting))
                elif isinstance(locals()[setting], tuple):
                    locals()[setting] += (getattr(module, setting))
                else:
                    print "Overriding %s" % setting
                    locals()[setting] = getattr(module, setting)
            else:
                locals()[setting] = getattr(module, setting)
        elif setting == 'additional_settings':
            additional_settings += getattr(module, setting)
