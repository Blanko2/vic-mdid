from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', m_main, name="mobile-main"),
    url(r'search/results', m_search, name="mobile-search-results")
)
