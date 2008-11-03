from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^group/(?P<groupname>[-\w]+)/$', group_raw, name='data-group'),
)
