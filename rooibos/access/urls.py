from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^view/(?P<model_id>\d+)/(?P<object_id>\d+)/$', access_view, name='access_view'),
)
