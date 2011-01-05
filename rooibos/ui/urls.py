from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from views import *

urlpatterns = patterns('',
    url(r'^css/(?P<stylesheet>[-\w]+)/$', css, name='ui-css'),
    url(r'^api/select-record/', select_record, name='ui-api-select-record'),
    url(r'^tag/(?P<type>\d+)/(?P<id>\d+)/', add_tags, name='ui-add-tags'),
    url(r'^tag/remove/(?P<type>\d+)/(?P<id>\d+)/', remove_tag, name='ui-remove-tag'),
    url(r'^manage/$', manage, name='ui-management'),
    url(r'^options/$', options, name='ui-options'),
    url(r'^clear-selected/$', clear_selected_records, name='ui-clear-selected'),
    url(r'^delete-selected/$', delete_selected_records, name='ui-delete-selected'),
    url(r'^report-problem/$', direct_to_template, {'template': 'ui_report_problem.html'}, name='ui-report-problem'),
)
