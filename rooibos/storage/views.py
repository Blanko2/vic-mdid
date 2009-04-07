from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.cache import cache_control
from rooibos.access import accessible_ids
from rooibos.data.models import Collection
from models import Media, Storage
from django.shortcuts import _get_queryset

@cache_control(max_age=3600)
def retrieve(request, recordid, record, mediaid, media):    
    mediaobj = get_object_or_404(Media.objects.filter(id=mediaid,
                                 record__id=recordid,
                                 record__collection__id__in=accessible_ids(request.user, Collection),
                                 storage__id__in=accessible_ids(request.user, Storage)).distinct())
    content = mediaobj.load_file()
    if content:
        return HttpResponse(content=content, mimetype=str(mediaobj.mimetype))
    else:
        return HttpResponseRedirect(mediaobj.get_absolute_url())
