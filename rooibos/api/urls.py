from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    url(r'^about/$', about),
    url(r'^collections(/(?P<id>\d+))?$', collections),
    url(r'^login/$', login),
    url(r'^logout/$', logout),
    url(r'^search/$', search),
    url(r'^search(/(?P<id>\d+)/(?P<name>[\w-]+))?/$', search),
    url(r'^record/(?P<id>\d+)/(?P<name>[-\w]+)/$', record),
    url(r'^presentations/currentuser/$', presentations_for_current_user),
    url(r'^presentation/(?P<id>\d+)/$', presentation_detail),
)
