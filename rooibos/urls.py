from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from rooibos.ui.views import main
from django.conf import settings

urlpatterns = patterns('',    
    (r'^$', main),
    
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', name='logout'),
    url(r'^admin/(.*)', admin.site.root, name='admin'),
    
    (r'^ui/', include('rooibos.ui.urls')),    
    (r'^acl/', include('rooibos.access.urls')),    
    (r'^explore/', include('rooibos.solr.urls')),
    (r'^media/', include('rooibos.storage.urls')),
    (r'^data/', include('rooibos.data.urls')),
    (r'^legacy/', include('rooibos.legacy.urls')),
    (r'^nasa/', include('rooibos.nasa.urls')),
    (r'^powerpoint/', include('rooibos.powerpoint.urls')),
    (r'^presentation/', include('rooibos.presentation.urls')),
    (r'^viewers/', include('rooibos.viewers.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': 'static'}),
    )
