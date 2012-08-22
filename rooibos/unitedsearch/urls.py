from django.conf.urls.defaults import *
from views import usViewer
import external.digitalnz

dnzviewer = usViewer(external.digitalnz)

urlpatterns = patterns('',
	url(r'^digitalnz/', include(dnzviewer.urlpatterns))
)
