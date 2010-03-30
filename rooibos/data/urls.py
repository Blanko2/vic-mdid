from django.conf.urls.defaults import *
from django.contrib.syndication.views import feed
from django.views.generic.simple import direct_to_template
from views import *
from feeds import GroupFeed

feeds = {
    'collection': GroupFeed,
}

urlpatterns = patterns('',
    url(r'^collections/$', collections, name='data-collections'),
    url(r'^collection/(?P<id>\d+)/(?P<name>[-\w]+)/$', collection_raw, name='data-collection'),
    url(r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/$', record, name='data-record'),
    url(r'^record-preview/(?P<id>\d+)/$', record_preview, name='data-record-preview'),
    url(r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/edit/$', record, kwargs={'edit': True}, name='data-record-edit'),
    url(r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/edit/(?P<contexttype>\w+\.\w+)/(?P<contextid>\d+)/(?P<contextname>[-\w]+)/$', record, kwargs={'edit': True}, name='data-record-edit-context'),
    url(r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/edit/personal/$', record, kwargs={'edit': True, 'personal': True}, name='data-record-edit-personal'),
    url(r'^record/new/$', record, kwargs={'id': None, 'name': None, 'edit': True}, name='data-record-new'),
    url(r'^import/$', data_import, name='data-import'),
    url(r'^import/(?P<file>[\w\d]{32})/$', data_import_file, name='data-import-file'),
    (r'^feeds/(?P<url>.*)/$', feed, {'feed_dict': feeds}),
)
