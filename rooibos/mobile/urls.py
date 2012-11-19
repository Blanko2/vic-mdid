from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', m_main, name="mobile-main"),
    url(r'search/results', m_search, name="mobile-search-results"),
    url(r'presentation/browse', m_browse, name="mobile-presentation-browse"),
    url(r'^search/(?P<sid>[a-z0-9A-Z,]*)/results', union_search, name="mobile-union-search")
)
