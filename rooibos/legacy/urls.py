from django.conf.urls.defaults import *
from views import soap

urlpatterns = patterns('',
    url(r'^WebServices/ImageViewer.asmx/Login$', soap),
)
