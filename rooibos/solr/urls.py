from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^search/$', search, name='solr-search'),
    url(r'^search/(?P<group>.*)/$', search, name='solr-search-group'),
)
