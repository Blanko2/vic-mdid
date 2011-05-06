from django import forms
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from rooibos.presentation.models import Presentation
import re


class MegazineViewer(Viewer):

    title = "Megazine Viewer"
    weight = 20
    is_embeddable = True

    #def get_options_form(self):
    #
    #    #class OptionsForm(forms.Form):
    #    #    pass
    #    #
    #    #return OptionsForm
    #
    #    return None
    #
    #
    def embed_script(self, request):

        divid = request.GET.get('id', 'unknown')

        server = (('https' if request.META.get('HTTPS', 'off') == 'on' else 'http') +
            '://' + request.META['HTTP_HOST'])

        return render_to_response('megazine_viewer.js',
                                  {'presentation': self.obj,
                                   'server_url': server,
                                   'anchor_id': divid,
                                   },
                                  context_instance=RequestContext(request))


@register_viewer('megazine', MegazineViewer)
def megazine(obj, request, objid=None):
    if not getattr(settings, 'MEGAZINE_PUBLIC_KEY', None):
        return None
    if obj:
        if not isinstance(obj, Presentation):
            return None
    else:
        obj = Presentation.get_by_id_for_request(objid, request)
        if not obj:
            return None
    return MegazineViewer(obj, request.user)
