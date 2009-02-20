from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^get/(?P<record>[-\w]+)/(?P<media>[-\w]+)/$', retrieve, name='storage-retrieve'),
)
