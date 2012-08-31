from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', m_main, name="mobile-main")
)
