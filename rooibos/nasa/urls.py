from django.conf.urls.defaults import *
from views import *

urlpatterns = patterns('',
    url(r'^nix/search/', search, name='nasa-nix-search'),
)
