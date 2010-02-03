from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from views import *

urlpatterns = patterns('',
    url(r'^api/select-record/', select_record, name='ui-api-select-record'),
    url(r'^tag/(?P<type>\d+)/(?P<id>\d+)/', add_tags, name='ui-add-tags'),
    url(r'^tag/remove/(?P<type>\d+)/(?P<id>\d+)/', remove_tag, name='ui-remove-tag'),
    url(r'^manage/$', manage, name='ui-management'),
)
