from django import forms
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from models import Presentation
import re
import math



class PresentationViewer(Viewer):

    title = "View"
    weight = 100
    is_embeddable = False

    def view(self, request):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        return render_to_response('presentation_viewer.html',
                                  {'presentation': self.obj,
                                   'return_url': return_url,
                                },
                            context_instance=RequestContext(request))


@register_viewer('presentationviewer', PresentationViewer)
def presentationviewer(obj, request, objid=None):
    if obj:
        if not isinstance(obj, Presentation):
            return None
    else:
        obj = Presentation.get_by_id_for_request(objid, request)
        if not obj:
            return None
    return PresentationViewer(obj, request.user)
