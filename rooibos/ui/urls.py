from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from views import *

urlpatterns = patterns('',
    url(r'^csshover.htc', direct_to_template, {'template': 'csshover.htc', 'mimetype': 'text/x-component'}, name='ui-csshover-htc'),
)
