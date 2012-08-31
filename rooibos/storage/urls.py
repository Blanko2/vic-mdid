from django.conf.urls.defaults import *
from pseudostreaming import retrieve_pseudostream
from views import *
#from viewers import mediaplayer_script

urlpatterns = patterns('',
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/(?P<mediaid>\d+)/(?P<media>[-\w]+)/$', retrieve, name='storage-retrieve'),
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/(?P<width>\d{1,5})x(?P<height>\d{1,5})/$', retrieve_image, name='storage-retrieve-image'),
    url(r'^get/(?P<recordid>\d+)/(?P<record>[-\w]+)/$', retrieve_image, name='storage-retrieve-image-nosize'),
    url(r'^upload/(?P<recordid>\d+)/(?P<record>[-\w]+)/$', media_upload, name='storage-media-upload'),
    url(r'^delete/(?P<mediaid>\d+)/(?P<medianame>[-\w]+)/$', media_delete, name='storage-media-delete'),
    url(r'^thumb/(?P<id>\d+)/(?P<name>[-\w]+)/$', record_thumbnail, name='storage-thumbnail'),
    url(r'^proxy/create/$', create_proxy_url_view),
    url(r'^proxy/(?P<uuid>[0-9a-f-]+)/$', call_proxy_url, name='storage-proxyurl'),
    url(r'^pseudostream/(?P<recordid>\d+)/(?P<record>[-\w]+)/(?P<mediaid>\d+)/(?P<media>[-\w]+)/$', retrieve_pseudostream, name='storage-retrieve-pseudostream'),
    url(r'^manage/$', manage_storages, name='storage-manage'),
    url(r'^import/$', import_files, name='storage-import'),
    url(r'^storage/(?P<storageid>\d+)/(?P<storagename>[-\w]+)/$', manage_storage, name='storage-manage-storage'),
    url(r'^storage/new/$', manage_storage, name='storage-create-storage'),
    url(r'^match-up-files/$', match_up_files, name='storage-match-up-files'),
    url(r'^analyze/(?P<id>\d+)/(?P<name>[-\w]+)/$', analyze, name='storage-analyze'),
    url(r'^records-without-media/$', find_records_without_media, name='storage-find-records-without-media'),
    #url(r'^mediaplayer-script/$', mediaplayer_script, name='storage-mediaplayer-script'),
)
