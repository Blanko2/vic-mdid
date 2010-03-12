from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.views.static import serve
from django.views.decorators.cache import cache_control
from rooibos.ui.views import main
from rooibos.access.views import login, logout


admin.autodiscover()

apps = filter(lambda a: a.startswith('apps.'), settings.INSTALLED_APPS)
apps_showcases = list(s[5:].replace('.', '-') + '-showcase.html' for s in apps)

# Cache static files
serve = cache_control(max_age=365 * 24 * 3600)(serve)


urls = [
    url(r'^$', main, {'HELP': 'frontpage'}, name='main'),
    url(r'^about/', direct_to_template, {'template': 'about.html'}, name='about'),
    url(r'^showcases/', direct_to_template, {'HELP': 'showcases',
                                             'template': 'showcases.html',
                                             'extra_context': {'applications': apps_showcases}}, name='showcases'),
    url(r'^login/$', login, {'HELP': 'logging-in', 'SSL': True}, name='login'),
    url(r'^logout/$', logout, {'HELP': 'logging-out', 'next_page': '/'}, name='logout'),
    url(r'^admin/(.*)', admin.site.root, {'SSL': True}, name='admin'),

    (r'^ui/', include('rooibos.ui.urls')),
    (r'^acl/', include('rooibos.access.urls')),
    (r'^explore/', include('rooibos.solr.urls')),
    (r'^media/', include('rooibos.storage.urls')),
    (r'^data/', include('rooibos.data.urls')),
    (r'^legacy/', include('rooibos.legacy.urls')),
    (r'^presentation/', include('rooibos.presentation.urls')),
    (r'^viewers/', include('rooibos.viewers.urls')),
    (r'^workers/', include('rooibos.workers.urls')),
    (r'^convert/', include('rooibos.converters.urls')),
    (r'^api/', include('rooibos.api.urls')),
    (r'^profile/', include('rooibos.userprofile.urls')),
    (r'^federated/', include('rooibos.federatedsearch.urls')),
    (r'^nasa/', include('rooibos.federatedsearch.nasa.urls')),
    (r'^flickr/', include('rooibos.federatedsearch.flickr.urls')),
    (r'^artstor/', include('rooibos.federatedsearch.artstor.urls')),

    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_DIR}, name='static'),
    ]

if 'apps.jmutube' in apps:
    urls.append(url(r'^jmutube/', include('apps.jmutube.urls')))
if 'apps.svohp' in apps:
    urls.append(url(r'^svohp/', include('apps.svohp.urls')))
if 'apps.ovc' in apps:
    urls.append(url(r'^ovc/', include('apps.ovc.urls')))

urlpatterns = patterns('', *urls)
