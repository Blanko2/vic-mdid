from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpRequest, HttpResponseNotAllowed, HttpResponseForbidden
from django.utils import simplejson
from django.core import serializers
from django.db.models import Q
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
from django.views.decorators.cache import cache_control
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


def _presentation_item_as_json(item, owner=None, process_url=lambda url: url):
    data = dict(
                id=item.record.id,
                name=item.record.name,
                title=item.title or 'Untitled',
                thumbnail=process_url(item.record.get_thumbnail_url()),
                image=process_url(item.record.get_image_url()),
                metadata=[
                    dict(
                        label=value.resolved_label,
                        value=value.value
                        )
                    for value in item.get_fieldvalues(owner=owner)
                ]
            )
    annotation = item.annotation
    if annotation:
        data['metadata'].append(dict(label='Annotation', value=annotation))
    return data
  
def _presentation_items_as_json(items, owner=None, process_url=lambda url: url):
    return [_presentation_item_as_json(item, owner, process_url) for item in items]


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


@cache_control(no_cache=True)
@json_view
def presentation_detail(request, id):    
    p = Presentation.get_by_id_for_request(id, request)
    if not p:
        return dict(result='error')
    
    flash = request.GET.get('flash') == '1'
    
    # Propagate the flash URL paramater into all image URLs to control the "Vary: cookie" header
    # that breaks caching in Flash/Firefox.  Also add the username from the request to make sure
    # different users don't use each other's cached images.
    def add_flash_parameter(url, request):
        u = create_proxy_url_if_needed(url, request)
        if flash:
            u = u + ('&' if u.find('?') > -1 else '?') \
                  + ('flash=1&user=%s' % (request.user.id if request.user.is_authenticated() else -1))
        return u
    
    return dict(id=p.id,
                name=p.name,
                title=p.title,
                hidden=p.hidden,
                description=p.description,
                created=p.created.isoformat(),
                modified=p.modified.isoformat(),
                content=_presentation_items_as_json(p.items.select_related('record').filter(hidden=False),
                                         owner=request.user if request.user.is_authenticated() else None,
                                         process_url=lambda url:add_flash_parameter(url, request))
            )


@cache_control(no_cache=True)
@json_view
def keep_alive(request):
    return dict(user=request.user.username if request.user else '')
    
    
@cache_control(no_cache=True)        
def autocomplete_user(request):
    query = request.GET.get('q', '').lower()
    try:
        limit = max(10, min(25, int(request.GET.get('limit', '10'))))
    except ValueError:
        limit = 10
    if not query or not request.user.is_authenticated():
        return ''
    users = list(User.objects.filter(username__istartswith=query).order_by('username').values_list('username', flat=True)[:limit])
    if len(users) < limit:
        users.extend(User.objects.filter(~Q(username__istartswith=query), username__icontains=query)
                     .order_by('username').values_list('username', flat=True)[:limit-len(users)])
    return HttpResponse(content='\n'.join(users))
