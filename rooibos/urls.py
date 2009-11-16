from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template
from rooibos.ui.views import main


admin.autodiscover()

urls = [
    url(r'^$', main, name='main'),
    url(r'^about/', direct_to_template, {'template': 'about.html'}, name='about'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'SSL': True}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),
    url(r'^admin/(.*)', admin.site.root, {'SSL': True}, name='admin'),

    (r'^ui/', include('rooibos.ui.urls')),
    (r'^acl/', include('rooibos.access.urls')),
    (r'^explore/', include('rooibos.solr.urls')),
    (r'^media/', include('rooibos.storage.urls')),
    (r'^data/', include('rooibos.data.urls')),
    (r'^legacy/', include('rooibos.legacy.urls')),
    (r'^nasa/', include('rooibos.nasa.urls')),
    (r'^presentation/', include('rooibos.presentation.urls')),
    (r'^viewers/', include('rooibos.viewers.urls')),
    (r'^convert/', include('rooibos.converters.urls')),
    (r'^api/', include('rooibos.api.urls')),
    (r'^flickr/', include('rooibos.flickr.urls')),
    (r'^artstor/', include('rooibos.artstor.urls')),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_DIR}, name='static'),
    ]

if 'apps.jmutube' in settings.INSTALLED_APPS:
    urls.append(url(r'^jmutube/', include('apps.jmutube.urls')))
if 'apps.svohp' in settings.INSTALLED_APPS:
    urls.append(url(r'^svohp/', include('apps.svohp.urls')))

urlpatterns = patterns('', *urls)
