from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    #url(r'^$', m_main, name="mobile-main"),
    #url(r'search/results', m_search, name="mobile-search-results"),
    #url(r'presentation/browse', m_browse, name="mobile-presentation-browse"),
    #url(r'^search/(?P<sid>[a-z0-9A-Z,]*)/results', union_search, name="mobile-union-search"),
    #url(r'^searchredirect/',redirect,name="mobile-search-redirect"),
    url(r'^$', m_main, name="mobile-main"),
    url(r'search/results', m_search_redirect, name="mobile-search-redirect"),
    url(r'search/(?P<database>[a-z0-9A-Z]*)/results', m_search, name="mobile-search"),
    url(r'search/image/(?P<database>[a-z0-9A-Z]*)', m_showImage, name="mobile-image-view"),
    url(r'presentations/list', m_browse, name="mobile-presentation-list")
)
