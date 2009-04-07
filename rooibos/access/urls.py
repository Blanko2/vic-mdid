from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^view/(?P<app_label>[\w-]+)/(?P<model>[\w-]+)/(?P<id>\d+)/(?P<name>[\w-]+)/(?:(?P<foruser>.+)/)?$',
        access_view, name='access_view'),
)
