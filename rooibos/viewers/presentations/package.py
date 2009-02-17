from rooibos.presentation.models import Presentation
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404


class PackagePresentation(object):

    title = "Package"
    
    def __init__(self):
        pass
    
    def analyze(self, obj):
        if not isinstance(obj, Presentation):
            return False
        
        return True

    def execute(self, obj):
        return None
    
    def url(self):
        return url(r'^package/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self, name='viewers-package')
    
    def url_for_obj(self, obj):
        return reverse('viewers-package', kwargs={'id': obj.id, 'name': obj.name})
    
    def __call__(self, request, *args, **kwargs):
        return HttpResponse(content='Hello world!')