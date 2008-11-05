from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from rooibos.settings import WEBSERVICE_NAMESPACE, SECURE_LOGIN
from views import *
from rooibos.storage.views import retrieve

urlpatterns = patterns('',
    (r'^WebServices/ImageViewer.asmx/GetInfo$', direct_to_template,
        {'template': 'imageviewer_getinfo.xml',
         'extra_context': {'namespace': WEBSERVICE_NAMESPACE, 'securelogin': SECURE_LOGIN},
         'mimetype': 'text/xml'}),
    (r'^WebServices/ImageViewer.asmx/Login$', imageviewer_login, {}),
    (r'^WebServices/ImageViewer.asmx/GetSlideshow$', imageviewer_getslideshow, {}),
    url(r'^image/(?P<record>[-\w]+)/(?P<media>[-\w]+)/$', retrieve, name='legacy-image'),
)
