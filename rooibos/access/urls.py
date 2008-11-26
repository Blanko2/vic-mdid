from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^view/(?P<app_label>[\w-]+)/(?P<model>[\w-]+)/(?P<object>[\w-]+)/$', access_view, name='access_view'),
)
