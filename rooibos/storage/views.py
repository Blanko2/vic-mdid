from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.cache import cache_control
from rooibos.access import accessible_ids
from rooibos.data.models import Group
from models import Media, Storage

@cache_control(max_age=3600)
def retrieve(request, record, media):
    mediaobj = get_object_or_404(Media.objects.filter(name=media,
                                 record__name=record,
                                 record__group__id__in=accessible_ids(request.user, Group),
                                 storage__id__in=accessible_ids(request.user, Storage)).distinct())
    content = mediaobj.load_file()
    if content:
        return HttpResponse(content=content, mimetype=str(mediaobj.mimetype))
    else:
        return HttpResponseRedirect(mediaobj.get_absolute_url())
