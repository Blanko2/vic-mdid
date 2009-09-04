from django.conf.urls.defaults import patterns, url
from django.conf import settings

from views import start, stop

urlpatterns = patterns('',
    url(r'^start/', start, name='impersonation-start'),
    url(r'^stop/', stop, name='impersonation-stop'),
)
