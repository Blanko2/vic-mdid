from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^options/(?P<groupname>[-\w]+)/$', powerpoint_options, name='powerpoint-options'),    
    url(r'^generate/(?P<groupname>[-\w]+)/(?P<template>.+)/$', powerpoint_generator, name='powerpoint-generator'),    
)
