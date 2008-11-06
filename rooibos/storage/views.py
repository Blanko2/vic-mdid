from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404
from models import Media

def retrieve(request, record, media):
    mediaobj = get_object_or_404(Media, name=media, record__name=record)
    content = mediaobj.load_file()
    if content:
        return HttpResponse(content=content, mimetype=str(mediaobj.mimetype))
    else:
        return HttpResponseRedirect(mediaobj.get_absolute_url())
