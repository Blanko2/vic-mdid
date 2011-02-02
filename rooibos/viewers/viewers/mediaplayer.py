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
import re


class MediaPlayer(object):

    title = "Media Player"
    weight = 20

    _supported_mimetypes = ('video/mp4', 'video/quicktime', 'video/x-m4v', 'video/x-flv',
                            'audio/mpeg', 'audio/x-aac')
    _url_name = 'viewers-mediaplayer'
    _url_pattern = r'^mediaplayer/(?P<id>[\d]+)/(?P<name>[-\w]+)/$'

    def __init__(self):
        pass

    def _check_playable(self, user, media):
        r, w, m, restrictions = get_effective_permissions_and_restrictions(user, media.storage)
        return not restrictions or restrictions.get('download') != 'only'

    def analyze(self, obj, user):
        if not isinstance(obj, Record):
            return NO_SUPPORT
        media = obj.media_set.filter(storage__in=filter_by_access(user, Storage),
                                     mimetype__in=self._supported_mimetypes)
        return FULL_SUPPORT if any(self._check_playable(user, m) for m in media) else NO_SUPPORT

    def url(self):
        return url(self._url_pattern, self.view, name=self._url_name)

    def url_for_obj(self, obj):
        return reverse(self._url_name, kwargs={'id': obj.id, 'name': obj.name})

    def _get_record_and_media(self, request, id, mediaid=None):
        record = Record.get_or_404(id, request.user)
        storages = filter_by_access(request.user, Storage)
        media = record.media_set.filter(storage__in=filter_by_access(request.user, Storage),
                                        mimetype__in=self._supported_mimetypes).order_by('bitrate')
        if mediaid:
            media = media.filter(id=mediaid)
        media = filter(lambda m: self._check_playable(request.user, m), media)
        if not media:
            raise Http404()
        return (record, media)

    def view(self, request, id, name, template='mediaplayer/mediaplayer.html'):
        record, media = self._get_record_and_media(request, id)

        selectedmedia = media[int(request.GET.get('media', 0))]
        delivery_url = selectedmedia.get_delivery_url()
        streaming_server = None
        streaming_media = None
        if delivery_url.startswith('rtmp://'):
            try:
                streaming_server, prot, streaming_media = re.split('/(mp[34]:)', delivery_url)
                streaming_media = prot + re.sub(r'\.mp3$', '', streaming_media)
            except ValueError:
                pass

        return render_to_response(template,
                                  {'record': record,
                                   'media': media,
                                   'next': request.GET.get('next'),
                                   'selectedmedia': selectedmedia,
                                   'delivery_url': delivery_url,
                                   'streaming_server': streaming_server,
                                   'streaming_media': streaming_media,
                                   'audio': selectedmedia.mimetype.startswith('audio/'),
                                   },
                                  context_instance=RequestContext(request))


class EmbeddedMediaPlayer(MediaPlayer):

    title = "Embed Media Player"
    weight = 10

    _url_name = 'viewers-embeddedmediaplayer'
    _url_pattern = r'^embeddedmediaplayer/(?P<id>[\d]+)/(?P<name>[-\w]+)/$'

    def url(self):
        return [
            super(EmbeddedMediaPlayer, self).url(),
            url('embed/(?P<id>[\d]+)_(?P<mediaid>[\d]+)\.js/?$', self.embed_script, name='viewers-embeddedmediaplayer-script'),
        ]

    def view(self, request, id, name):
        return super(EmbeddedMediaPlayer, self).view(request, id, name, 'mediaplayer/embeddedmediaplayer.html')

    def embed_script(self, request, id, mediaid):
        try:
            record, media = self._get_record_and_media(request, id, mediaid)
        except Http404:
            return HttpResponseForbidden()

        selectedmedia = media[0]
        delivery_url = selectedmedia.get_delivery_url()
        streaming_server = None
        streaming_media = None

        server = (('https' if request.META.get('HTTPS', 'off') == 'on' else 'http') +
            '://' + request.META['HTTP_HOST'])

        if delivery_url.startswith('rtmp://'):
            try:
                streaming_server, prot, streaming_media = re.split('/(mp[34]:)', delivery_url)
                streaming_media = prot + re.sub(r'\.mp3$', '', streaming_media)
            except ValueError:
                pass
        if not '://' in delivery_url:
            delivery_url = server + delivery_url

        Activity.objects.create(event='mediaplayer-embed',
                                request=request,
                                content_object=selectedmedia)

        return render_to_response('mediaplayer/mediaplayer.js',
                                  {'record': record,
                                   'selectedmedia': selectedmedia,
                                   'delivery_url': delivery_url,
                                   'streaming_server': streaming_server,
                                   'streaming_media': streaming_media,
                                   'audio': selectedmedia.mimetype.startswith('audio/'),
                                   'server_url': server,
                                   'autoplay': request.GET.has_key('autoplay'),
                                   },
                                  context_instance=RequestContext(request))
