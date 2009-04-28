from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^manage/$', manage, name='presentation-manage'),
    url(r'^create/$', create, name='presentation-create'),
    url(r'^edit/(?P<id>\d+)/(?P<name>[-\w]+)/$', edit, name='presentation-edit'),
    url(r'^view/(?P<id>\d+)/(?P<name>[-\w]+)/$', view, name='presentation-view'),
)
