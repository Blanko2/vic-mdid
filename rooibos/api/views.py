from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpRequest, HttpResponseNotAllowed
from django.utils import simplejson
from django.core import serializers
from rooibos.ui import update_record_selection
from rooibos.util import safe_int, json_view
from rooibos.access import filter_by_access, accessible_ids, accessible_ids_list
from rooibos.storage.models import Storage, Media
from rooibos.data.models import Field, Collection, FieldValue, Record
from rooibos.solr.views import *
from rooibos.data.models import *
from rooibos.storage import get_thumbnail_for_record
from rooibos.storage.views import create_proxy_url_if_needed
from rooibos.presentation.models import Presentation
from rooibos.access import filter_by_access
from django.conf import settings
from django.contrib.auth import authenticate
import django.contrib.auth


@json_view
def collections(request, id=None):
    if id:
        collections = filter_by_access(request.user, Collection.objects.filter(id=id))
    else:
        collections = filter_by_access(request.user, Collection)
    return {
        'collections': [
            dict(id=c.id,
                 name=c.name,
                 title=c.title,
                 owner=c.owner,
                 hidden=c.hidden,
                 description=c.description,
                 agreement=c.agreement,
                 children=list(c.children.all().values_list('id', flat=True)),
                 )
            for c in collections]
    }


@json_view
def login(request):
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        if (user is not None) and user.is_active:
            django.contrib.auth.login(request, user)
            return dict(result='ok', sessionid=request.session.session_key)
        else:
            return dict(result='Login failed')
    else:
        return dict(result='Invalid method. Use POST.')


@json_view
def logout(request):
    django.contrib.auth.logout(request)
    return dict(result='ok')


def _record_as_json(record, owner=None, context=None, process_url=lambda url: url):
    return dict(
                id=record.id,
                name=record.name,
                title=record.title,
                thumbnail=process_url(record.get_thumbnail_url()),
                image=process_url(record.get_image_url()),
                metadata=[
                    dict(
                        label=value.resolved_label,
                        value=value.value
                        )
                    for value in record.get_fieldvalues(owner=owner, context=context)
                ]
            )

def _records_as_json(records, owner=None, context=None, process_url=lambda url: url):
    return [_record_as_json(record, owner, context, process_url) for record in records]


@json_view
def api_search(request, id=None, name=None):
    hits, records, viewmode = search(request, id, name, json=True)
    return dict(hits=hits,
                records=_records_as_json(records, owner=request.user))


@json_view
def record(request, id, name):
    record = get_object_or_404(Record.objects.filter(id=id, collection__id__in=accessible_ids(request.user, Collection)))
#    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))
    return dict(record=_record_as_json(record, owner=request.user))


@json_view
def presentations_for_current_user(request):
    if request.user.is_anonymous():
        return dict(presentations=[])
    presentations = Presentation.objects.filter(owner=request.user).order_by('title')
    return {
        'presentations': [
            dict(id=p.id,
                 name=p.name,
                 title=p.title,
                 hidden=p.hidden,
                 description=p.description,
                 created=p.created.isoformat(),
                 modified=p.modified.isoformat())
            for p in presentations
        ]
    }


@json_view
def presentation_detail(request, id):
    p = get_object_or_404(Presentation.objects.filter(owner=request.user), id=id)
    return dict(id=p.id,
                name=p.name,
                title=p.title,
                hidden=p.hidden,
                description=p.description,
                created=p.created.isoformat(),
                modified=p.modified.isoformat(),
                content=_records_as_json(map(lambda i: i.record, p.items.select_related('record').filter(hidden=False)),
                                         owner=request.user,
                                         context=p,
                                         process_url=lambda url:create_proxy_url_if_needed(url, request))
            )
