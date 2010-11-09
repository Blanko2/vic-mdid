from __future__ import with_statement
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from rooibos.access import accessible_ids, accessible_ids_list, check_access, filter_by_access, get_effective_permissions_and_restrictions
from rooibos.data.models import Record, Collection, standardfield, get_system_field
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.storage.models import Storage
from rooibos.util import json_view


class AudioPlayer(object):

    title = "Audio Player"
    weight = 20

    def __init__(self):
        pass

    def _check_playable(self, user, media):
        r, w, m, restrictions = get_effective_permissions_and_restrictions(user, media.storage)
        return not restrictions or restrictions.get('download') != 'only'

    def analyze(self, obj, user):
        if not isinstance(obj, Record):
            return NO_SUPPORT
        audios = obj.media_set.filter(
                                     storage__in=filter_by_access(user, Storage),
                                     mimetype__in=('audio/mpeg',))
        for audio in audios:
            if self._check_playable(user, audio):
                return FULL_SUPPORT
        return NO_SUPPORT

    def url(self):
        return url(r'^audioplayer/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-audioplayer')

    def url_for_obj(self, obj):
        return reverse('viewers-audioplayer', kwargs={'id': obj.id, 'name': obj.name})

    def _get_record_and_media(self, request, id, name):
        record = Record.get_or_404(id, request.user)
        storages = filter_by_access(request.user, Storage)
        media = record.media_set.filter(
                                     storage__in=filter_by_access(request.user, Storage),
                                     mimetype__in=('audio/mpeg',)).order_by('bitrate')
        media = filter(lambda m: self._check_playable(request.user, m), media)
        if not media:
            raise Http404()
        return (record, media)

    def view(self, request, id, name):
        record, media = self._get_record_and_media(request, id, name)
        return render_to_response('audioplayer/audioplayer.html',
                                  {'record': record,
                                   'media': media,
                                   'next': request.GET.get('next'),
                                   'selectedmedia': media[int(request.GET.get('audio', 0))],
                                   },
                                  context_instance=RequestContext(request))
