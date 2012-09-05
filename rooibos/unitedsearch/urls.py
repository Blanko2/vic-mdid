from django.conf.urls.defaults import *
from views import usViewer, union_search, union_select
import searchers

searchersurlpatterns = patterns('', *[url(r'^' + searcher.identifier + '/', include(usViewer(searcher, "united:searchers:%s" % searcher.identifier), namespace=searcher.identifier)) for searcher in searchers.all])

urlpatterns = patterns('',
	url(r'^searchers/', include(searchersurlpatterns, namespace="searchers")),
	url(r'^union/(?P<sid>[a-z0-9A-Z,]*)/search', union_search, name="union-search"),
	url(r'^union/(?P<sid>[a-z0-9A-Z,]*)/select', union_select, name="union-select"),
)
