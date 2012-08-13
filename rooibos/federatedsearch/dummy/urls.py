from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
	url(r'^search/', views.search, name='dummy-search'),
#	url(r'^select/', nix_select_record, name='dummy-select'),
)
