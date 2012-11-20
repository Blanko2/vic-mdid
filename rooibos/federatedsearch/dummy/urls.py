from django.conf.urls.defaults import *
import views

urlpatterns = patterns('',
	url(r'^search/', views.search, name='dummy-search'),
	url(r'^select/', views.select, name='dummy-select'),
)
