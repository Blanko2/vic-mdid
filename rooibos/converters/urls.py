from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^$', main, name='converters-main'),
    url(r'^powerpoint-main/$', powerpoint_main, name='powerpoint-main'),
    url(r'^image-main/$', image_main, name='image-main'),
)