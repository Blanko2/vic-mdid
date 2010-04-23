from datetime import datetime, timedelta
from django import forms
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib.csrf.middleware import csrf_exempt
from django.core.urlresolvers import resolve, reverse
from django.db.models import Count, Q
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseServerError, HttpResponseForbidden
from django.shortcuts import _get_queryset, get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.views.decorators.cache import cache_control
from models import Media, Storage, TrustedSubnet, ProxyUrl
from rooibos.access import accessible_ids, filter_by_access, get_effective_permissions_and_restrictions, get_accesscontrols_for_object
from rooibos.contrib.ipaddr import IP
from rooibos.data.models import Collection, Record, Field, FieldValue, CollectionItem, standardfield
from rooibos.storage import get_image_for_record, get_thumbnail_for_record
from rooibos.util import json_view
import logging
import os
import uuid
import mimetypes

#def expire_header(seconds=3600):
#    return (datetime.utcnow() + timedelta(0, seconds)).strftime('%a, %d %b %Y %H:%M:%S GMT')


def add_content_length(func):
    def _add_header(request, *args, **kwargs):
        response = func(request, *args, **kwargs)
        if type(response) == HttpResponse:
            response['Content-Length'] = len(response.content)
        return response
    return _add_header


@add_content_length
@cache_control(private=True, max_age=3600)
def retrieve(request, recordid, record, mediaid, media):

    # check if media exists    
    mediaobj = get_object_or_404(Media.objects.filter(id=mediaid, record__id=recordid))
    
    # check permissions
    try:
        mediaobj = Media.objects.get(id=mediaid,
                                 record__id=recordid,
                                 record__collection__id__in=accessible_ids(request.user, Collection),
                                 storage__id__in=accessible_ids(request.user, Storage))
    except Media.DoesNotExist:
        return HttpResponseForbidden()

    r, w, m, restrictions = get_effective_permissions_and_restrictions(request.user, mediaobj.storage)
    # if size restrictions exist, no direct download of a media file is allowed
    if restrictions and (restrictions.has_key('width') or restrictions.has_key('height')):
        raise Http404()

    try:
        content = mediaobj.load_file()
    except IOError:
        raise Http404()
    
    if content:
        return HttpResponse(content=content, mimetype=str(mediaobj.mimetype))
    else:
        return HttpResponseRedirect(mediaobj.get_absolute_url())


@add_content_length
@cache_control(private=True, max_age=3600)
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
            mimetype = mimetypes.guess_type(file.name)[0] or file.content_type

            media = Media.objects.create(record=record,
                                         name=os.path.splitext(file.name)[0],
                                         storage=storage,
                                         mimetype=mimetype)
            media.save_file(file.name, file)

            if request.POST.get('swfupload') == 'true':
                return HttpResponse(content='ok', mimetype='text/plain')

            next = request.GET.get('next')
            return HttpResponseRedirect(next or '.')
    else:
        form = UploadFileForm()

    return render_to_response('storage_upload.html',
                              {'record': record,
                               'form': form,
                               },
                              context_instance=RequestContext(request))


@add_content_length
@cache_control(private=True, max_age=3600)
def record_thumbnail(request, id, name):
    record = get_object_or_404(Record.objects.filter(id=id,
        collection__id__in=accessible_ids(request.user, Collection)).distinct())

    media = get_thumbnail_for_record(record, request.user, crop_to_square=request.GET.has_key('square'))    
    if media:
        try:
            content = media.load_file()
            if content:
                return HttpResponse(content=content, mimetype=str(media.mimetype))
        except IOError, ex:
            pass
    return HttpResponseRedirect(reverse('static', args=['images/thumbnail_unavailable.png']))


@json_view
def create_proxy_url_view(request):
    if request.method == 'POST':
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


@login_required
def manage_storages(request):
    
    storages = get_list_or_404(filter_by_access(request.user, Storage, manage=True).order_by('title'))
    
    return render_to_response('storage_manage.html',
                          {'storages': storages,
                           },
                          context_instance=RequestContext(request))


@login_required
def manage_storage(request, storageid, storagename):
    
    storage = get_object_or_404(filter_by_access(request.user, Storage, manage=True), id=storageid)
    
    class StorageForm(forms.ModelForm):
        system = forms.CharField(widget=forms.Select(choices=[(s,s) for s in settings.STORAGE_SYSTEMS.keys()]))
        class Meta:
            model = Storage
            exclude = ('derivative',)
    
    form = StorageForm(instance=storage)
    
    return render_to_response('storage_edit.html',
                          {'storage': storage,
                           'form': form,
                           },
                          context_instance=RequestContext(request))



@csrf_exempt
@login_required
def import_files(request):

    available_storage = get_list_or_404(filter_by_access(request.user, Storage.objects.filter(master=None), write=True).order_by('title').values_list('id', 'title'))
    available_collections = get_list_or_404(filter_by_access(request.user, Collection, write=True).order_by('title').values_list('id', 'title'))
    
    class UploadFileForm(forms.Form):
        collection = forms.ChoiceField(choices=available_collections)
        storage = forms.ChoiceField(choices=available_storage)
        file = forms.FileField()
        create_records = forms.BooleanField(required=False)
        replace_files = forms.BooleanField(required=False, label='Replace files of same type')
        personal_records = forms.BooleanField(required=False)
        

    if request.method == 'POST':
        
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            
            collection = get_object_or_404(filter_by_access(request.user, Collection.objects.filter(id=form.cleaned_data['collection']), write=True))
            storage = get_object_or_404(filter_by_access(request.user, Storage.objects.filter(id=form.cleaned_data['storage']), write=True))
            create_records = form.cleaned_data['create_records']
            replace_files = form.cleaned_data['replace_files']
            personal_records = form.cleaned_data['personal_records']
            file = request.FILES['file']

            mimetype = mimetypes.guess_type(file.name)[0] or file.content_type

            owner = request.user if personal_records else None
            id = os.path.splitext(file.name)[0]

            # find record by identifier
            titlefield = standardfield('title')
            idfield = standardfield('identifier')
            idfields = standardfield('identifier', equiv=True)

            records = Record.by_fieldvalue(idfields, id).filter(collection=collection, owner=owner)
            result = "File skipped."
            record = None
            
            if len(records) == 1:
                # Matching record found
                record = records[0]
                media = record.media_set.filter(storage=storage, mimetype=mimetype)
                if len(media) == 0:
                    # No media yet
                    media = Media.objects.create(record=record,
                                                 name=id,
                                                 storage=storage,
                                                 mimetype=mimetype)
                    media.save_file(file.name, file)
                    result = "File added (Identifier '%s')." % id
                elif replace_files:
                    # Replace existing media
                    media = media[0]
                    media.delete_file()
                    media.save_file(file.name, file)
                    result = "File replaced (Identifier '%s')." % id
                else:
                    result = "File skipped, media files already attached."
            elif len(records) == 0:
                # No matching record found
                if create_records:
                    # Create a record
                    record = Record.objects.create(name=id, owner=owner)
                    CollectionItem.objects.create(collection=collection, record=record)
                    FieldValue.objects.create(record=record, field=idfield, value=id, order=0)
                    FieldValue.objects.create(record=record, field=titlefield, value=id, order=1)
                    media = Media.objects.create(record=record,
                                                 name=id,
                                                 storage=storage,
                                                 mimetype=mimetype)
                    media.save_file(file.name, file)
                    result = "File added to new record (Identifier '%s')." % id
                else:
                    result = "File skipped, no matching record found (Identifier '%s')." % id
            else:
                result = "File skipped, multiple matching records found (Identifier '%s')." % id
                # Multiple matching records found
                pass

            if request.POST.get('swfupload') == 'true':
                
                html = render_to_string('storage_import_file_response.html',
                                 {'result': result,
                                  'record': record,},
                                 context_instance=RequestContext(request)
                                 )
                
                return HttpResponse(content=simplejson.dumps(dict(status='ok', html=html)),
                                    mimetype='application/json')

            request.user.message_set.create(message=result)
            next = request.GET.get('next', request.get_full_path())
            return HttpResponseRedirect(next)
    else:
        form = UploadFileForm()

    return render_to_response('storage_import_files.html',
                              {'form': form,
                               },
                              context_instance=RequestContext(request))
