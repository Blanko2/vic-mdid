from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from models import Media

def retrieve(request, record, media):
    mediaobj = get_object_or_404(Media, name=media, record__name=record)
    response = HttpResponse(content='', mimetype=mediaobj.mimetype)
    return response
