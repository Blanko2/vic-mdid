from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from rooibos.ui.views import main
from django.conf import settings

urlpatterns = patterns('',
    
    (r'^$', main),
    
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),

    (r'^acl/', include('rooibos.access.urls')),    
    (r'^explore/', include('rooibos.solr.urls')),
    (r'^media/', include('rooibos.storage.urls')),
    (r'^data/', include('rooibos.data.urls')),
    (r'^legacy/', include('rooibos.legacy.urls')),
    (r'^nasa/', include('rooibos.nasa.urls')),
    (r'^powerpoint/', include('rooibos.powerpoint.urls')),

    # Uncomment the next line to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line for to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
    )
