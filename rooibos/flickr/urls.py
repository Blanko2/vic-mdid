from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', main, name='flickr-main'),
    url(r'^authorize/$', authorize, name='flickr-authorize'),
    url(r'^people(/(?P<username>[\w-]+))?/$', people, name='flickr-people'),
    url(r'^photosets(/(?P<id>[\w@]+))?/$', photosets, name='flickr-photosets'),
    url(r'^set(/(?P<setid>\d+))?/$', set, name='flickr-set'),
    url(r'^import-set/$', import_set_photos, name='flickr-import-set'),
)
