from django.conf.urls.defaults import *
from views import load_settings, store_settings

urlpatterns = patterns('',
    url(r'^load/$', load_settings, name='userprofile-load'),
    url(r'^store/$', store_settings, name='userprofile-store'),
)
