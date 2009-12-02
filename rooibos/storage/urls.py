from django.conf.urls.defaults import *
from pseudostreaming import retrieve_pseudostream
from views import *

urlpatterns = patterns('',
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/(?P<mediaid>\d+)/(?P<media>[-\w]+)/$', retrieve, name='storage-retrieve'),
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/((?P<width>\d{1,5})x(?P<height>\d{1,5})/)?$', retrieve_image, name='storage-retrieve-image'),
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/$', retrieve_image, name='storage-retrieve-image-nosize'),
    url(r'^upload/(?P<recordid>\d+)/(?P<record>[-\w]+)/$', media_upload, name='storage-upload'),
    url(r'^thumb/(?P<id>\d+)/(?P<name>[-\w]+)/$', record_thumbnail, name='storage-thumbnail'),
    url(r'^proxy/create/$', create_proxy_url_view),
    url(r'^proxy/(?P<uuid>[0-9a-f-]+)/$', call_proxy_url, name='storage-proxyurl'),
    url(r'^pseudostream/(?P<recordid>\d+)/(?P<record>[-\w]+)/(?P<mediaid>\d+)/(?P<media>[-\w]+)/$', retrieve_pseudostream, name='storage-retrieve-pseudostream'),
)
