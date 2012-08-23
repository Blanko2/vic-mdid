from django.conf.urls.defaults import *
from views import usViewer
import searchers

urlpatterns = patterns('', *[url(r'^' + searcher.identifier + '/', include(usViewer(searcher), namespace=searcher.identifier)) for searcher in searchers.all])
