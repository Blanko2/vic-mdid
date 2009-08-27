from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseNotAllowed, \
    HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.views.decorators.cache import cache_control
from django.template import RequestContext
from django.shortcuts import _get_queryset
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.core.urlresolvers import resolve
from django.conf import settings
from rooibos.access import accessible_ids, filter_by_access, get_effective_permissions_and_restrictions
from rooibos.data.models import Collection, Record
from rooibos.storage import get_image_for_record, get_thumbnail_for_record
from rooibos.contrib.ipaddr import IP
from rooibos.util import json_view
from models import Media, Storage, TrustedSubnet, ProxyUrl
import os
import uuid
from datetime import datetime


@cache_control(max_age=3600)
def retrieve(request, recordid, record, mediaid, media):
    mediaobj = get_object_or_404(Media.objects.filter(id=mediaid,
                                 record__id=recordid,
                                 record__collection__id__in=accessible_ids(request.user, Collection),
                                 storage__id__in=accessible_ids(request.user, Storage)).distinct())

    r, w, m, restrictions = get_effective_permissions_and_restrictions(request.user, mediaobj.storage)
    # if size restrictions exist, no direct download of a media file is allowed
    if restrictions and (restrictions.has_key('width') or restrictions.has_key('height')):
        raise Http404()

    content = mediaobj.load_file()
    if content:
        return HttpResponse(content=content, mimetype=str(mediaobj.mimetype))
    else:
        return HttpResponseRedirect(mediaobj.get_absolute_url())


def retrieve_image(request, recordid, record, width=None, height=None):

    width = int(width or '100000')
    height = int(height or '100000')

    media = get_image_for_record(recordid, request.user, width, height)

    if not media:
        raise Http404()

    # return resulting image
    content = media.load_file()
    if content:
        return HttpResponse(content=content, mimetype=str(media.mimetype))
    else:
        return HttpResponseServerError()


@login_required
def media_upload(request, recordid, record):

    available_storage = get_list_or_404(filter_by_access(request.user, Storage.objects.filter(master=None), write=True
                                         ).values_list('name','title'))
    record = get_object_or_404(Record.objects.filter(id=recordid,
        collection__id__in=accessible_ids(request.user, Collection)).distinct())

    class UploadFileForm(forms.Form):
        storage = forms.ChoiceField(choices=available_storage)
        file = forms.FileField()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            storage = Storage.objects.get(name=form.cleaned_data['storage'])
            file = request.FILES['file']

            media = Media.objects.create(record=record,
                                         name=os.path.splitext(file.name)[0],
                                         storage=storage,
                                         mimetype=file.content_type)
            media.save_file(file.name, file)

            next = request.GET.get('next')
            return HttpResponseRedirect(next or '.')
    else:
        form = UploadFileForm()

    return render_to_response('storage_upload.html',
                              {'record': record,
                               'form': form,
                               },
                              context_instance=RequestContext(request))



def record_thumbnail(request, id, name):
    record = get_object_or_404(Record.objects.filter(id=id,
        collection__id__in=accessible_ids(request.user, Collection)).distinct())

    media = get_thumbnail_for_record(record, request.user)

    if media:
        content = media.load_file()
        if content:
            return HttpResponse(content=content, mimetype=str(media.mimetype))
        else:
            return HttpResponseServerError()
    else:
        return HttpResponseRedirect('/static/images/nothumbnail.jpg')


@json_view
def create_proxy_url_view(request):
    if request.method == 'POST':

        print request.POST

        proxy_url = ProxyUrl.create_proxy_url(request.POST['url'],
                                     request.POST['context'],
                                     request.META['REMOTE_ADDR'],
                                     request.user)
        if not proxy_url:
            return HttpResponseForbidden()
        return dict(id=proxy_url.uuid)
    else:
        return HttpResponseNotAllowed(['POST'])

def create_proxy_url_if_needed(url, request):
    if hasattr(request, 'proxy_url'):
        return request.proxy_url.get_additional_url(url).get_absolute_url()
    else:
        return url

def call_proxy_url(request, uuid):
    context = request.GET.get('context')

    ip = IP(request.META['REMOTE_ADDR'])
    for subnet in TrustedSubnet.objects.all():
        if ip in IP(subnet.subnet):
            break
    else:
        return HttpResponseForbidden()

    proxy_url = get_object_or_404(ProxyUrl.objects.filter(uuid=uuid, context=context, subnet=subnet))
    proxy_url.last_access = datetime.now()
    proxy_url.save()

    view, args, kwargs = resolve(proxy_url.url)

    user = proxy_url.user
    user.backend = proxy_url.user_backend or settings.AUTHENTICATION_BACKENDS[0]
    login(request, user)

    request.proxy_url = proxy_url
    kwargs['request'] = request

    return view(*args, **kwargs)
