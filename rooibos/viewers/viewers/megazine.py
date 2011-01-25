from __future__ import with_statement
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from rooibos.access import filter_by_access, get_effective_permissions_and_restrictions
from rooibos.data.models import Record, Collection, standardfield, get_system_field
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.storage.models import Storage
from rooibos.util import json_view
from rooibos.statistics.models import Activity
from rooibos.presentation.models import Presentation
import re


class MegazinePlayer(object):

    title = "Megazine Player"
    weight = 20

    def __init__(self):
        pass

    def analyze(self, obj, user):
        if not isinstance(obj, Presentation):
            return NO_SUPPORT
        items = obj.cached_items()
        valid = filter(lambda i: not i.type or i.hidden, items)
        if len(valid) == 0:
            return NO_SUPPORT
        elif len(valid) < len(items):
            return PARTIAL_SUPPORT
        else:
            return FULL_SUPPORT

    def url(self):
        return [
            url(r'^megazine/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-megazine'),
            url(r'^megazine/(?P<id>[\d]+)/(?P<name>[-\w]+)/content/$', self.view_content, name='viewers-megazine-content'),
            ]

    def url_for_obj(self, obj):
        return reverse('viewers-megazine', kwargs={'id': obj.id, 'name': obj.name})

    def view(self, request, id, name, template='megazine/megazine.html'):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            if not request.user.is_authenticated():
                return HttpResponseRedirect(reverse('login') + '?next=' + request.get_full_path())
            else:
                return HttpResponseRedirect(return_url)

        return render_to_response(template,
                                  {'presentation': presentation,
                                   'next': request.GET.get('next'),
                                   },
                                  context_instance=RequestContext(request))

    def view_content(self, request, id, name):
        presentation = Presentation.get_by_id_for_request(id, request)
        if not presentation:
            raise Http404()

        items = presentation.items.select_related('record').filter(hidden=False)

        return render_to_response('megazine/megazine-content.mz3',
                                  {'items': items,
                                   },
                                  context_instance=RequestContext(request))
