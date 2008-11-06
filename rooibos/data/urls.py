from django.conf.urls.defaults import *
from django.contrib.syndication.views import feed
from views import *
from feeds import GroupFeed

feeds = {
    'group': GroupFeed,
}

urlpatterns = patterns('',
    url(r'^group/(?P<groupname>[-\w]+)/$', group_raw, name='data-group'),
    url(r'^record/(?P<recordname>[-\w]+)/$', record_raw, name='data-record'),
    (r'^feeds/(?P<url>.*)/$', feed, {'feed_dict': feeds}),
)
