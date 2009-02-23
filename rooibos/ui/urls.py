from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from views import *

urlpatterns = patterns('',
    url(r'^api/select-record/', select_record, name='ui-api-select-record'),
)
