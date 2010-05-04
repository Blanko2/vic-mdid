from __future__ import with_statement
from django.conf.urls.defaults import url
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext
from rooibos.access import accessible_ids, accessible_ids_list, check_access, filter_by_access
from rooibos.data.models import Record, Collection, standardfield, get_system_field
from rooibos.viewers import NO_SUPPORT, PARTIAL_SUPPORT, FULL_SUPPORT
from rooibos.storage.models import Storage
from rooibos.util import json_view


class VideoPlayer(object):

    title = "Video Player"
    weight = 20
    
    def __init__(self):
        pass
    
    def analyze(self, obj, user):
        if not isinstance(obj, Record):
            return NO_SUPPORT
        has_video = obj.media_set.filter(master=None,
                                         storage__in=filter_by_access(user, Storage),
                                         mimetype='video/mp4').count() > 0
        return FULL_SUPPORT if has_video else NO_SUPPORT
    
    def url(self):
        return [
            url(r'^videoplayer/(?P<id>[\d]+)/(?P<name>[-\w]+)/$', self.view, name='viewers-videoplayer'),
            url(r'^videoplayer/(?P<id>[\d]+)/(?P<name>[-\w]+)/rss/$', self.single_file_rss_feed, name='viewers-videoplayer-rss'),
            ]
    
    def url_for_obj(self, obj):
        return reverse('viewers-videoplayer', kwargs={'id': obj.id, 'name': obj.name})
    
    
    def _get_record_and_media(self, request, id, name):
        readable_collections = list(accessible_ids_list(request.user, Collection))

        if request.user.is_superuser:
            q = Q()
        else:
            q = ((Q(owner=request.user) if request.user.is_authenticated() else Q(owner=None)) |
                 Q(collection__id__in=readable_collections))
        record = get_object_or_404(Record.objects.filter(q, id=id).distinct())
    
        storages = filter_by_access(request.user, Storage)
        
        media = record.media_set.filter(master=None,
                                     storage__in=filter_by_access(request.user, Storage),
                                     mimetype='video/mp4')
        if not media:
            raise Http404()
            
        return (record, media[0])
        
    
    def view(self, request, id, name):        
        record, media = self._get_record_and_media(request, id, name)
        return render_to_response('videoplayer/videoplayer.html',
                                  {'record': record,
                                   'next': request.GET.get('next'),
                                   },
                                  context_instance=RequestContext(request))
    
    
    def single_file_rss_feed(self, request, id, name):
        record, media = self._get_record_and_media(request, id, name)
        return render_to_response('videoplayer/videoplayer.rss',
                                  { 'title': record.title,
                                   'url': record.get_absolute_url(),
                                   'playlist': ({'record': record,
                                                 'url': media.get_absolute_url(),
                                                 'mimetype': media.mimetype,
                                                 'size': media.file_size,
                                                 },) },
                                  context_instance = RequestContext(request))
