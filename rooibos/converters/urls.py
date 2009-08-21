from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', main, name='converters-main'),
    url(r'^powerpoint-main/$', powerpoint_main, name='powerpoint-main'),
)