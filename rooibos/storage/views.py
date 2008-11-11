from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from django.views.decorators.cache import cache_control
from rooibos.access.views import check_access
from models import Media

@cache_control(max_age=3600)
def retrieve(request, record, media):
    mediaobj = get_object_or_404(Media, name=media, record__name=record)
    check_access(request.user, mediaobj.storage, fail_if_denied=True)
    content = mediaobj.load_file()
    if content:
        return HttpResponse(content=content, mimetype=str(mediaobj.mimetype))
    else:
        return HttpResponseRedirect(mediaobj.get_absolute_url())
