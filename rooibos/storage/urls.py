from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/(?P<mediaid>\d+)/(?P<media>[-\w]+)/$', retrieve, name='storage-retrieve'),
)
