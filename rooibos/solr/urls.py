from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^search/$', search, name='solr-search'),
    url(r'^search/(?P<id>\d+)/(?P<name>[\w-]+)/$', search, name='solr-search-collection'),
    url(r'^api/search/$', search_json, name='api-solr-search'),
    url(r'^api/search/(?P<id>\d+)/(?P<name>[\w-]+)/$', search_json, name='api-solr-search-collection'),
    url(r'^selected/$', selected, name='solr-selected'),
    url(r'^browse/$', browse, name='solr-browse'),
    url(r'^browse/(?P<id>\d+)/(?P<name>[\w-]+)/$', browse, name='solr-browse-collection'),
    url(r'^overview/$', overview, name='solr-overview'),
)
