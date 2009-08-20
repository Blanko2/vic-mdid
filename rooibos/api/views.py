from datetime import datetime
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpRequest
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
from rooibos.presentation.models import Presentation

from rooibos.access import filter_by_access
from django.conf import settings

def about(request):
    return render_to_response('main.html',
                              {},
                              context_instance=RequestContext(request))

def collections(request, id=None):
    if id:
        collections = filter_by_access(request.user, Collection.objects.filter(id=id))
    else:
        collections = filter_by_access(request.user, Collection)
    json = serializers.serialize("json", collections)
    return HttpResponse(json, content_type='application/javascript')

def login(request):
    username = request.GET["username"]
    password = request.GET["password"]
    resp='{"response" : "not logged in"}'
    from django.contrib.auth import authenticate
    user = authenticate(username=username, password=password)
    if (user is not None) and user.is_active:
        from django.contrib.auth import login
        login(request, user)
        resp='{"sessionid" : '+request.session.session_key+'}'
    return HttpResponse(resp, content_type='application/javascript')

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    resp='[{"response" : "logged out"}]'
    return HttpResponse(resp, content_type='application/javascript')

def search(request, id=None, name=None, selected=False):
    collection = id and get_object_or_404(filter_by_access(request.user, Collection), id=id) or None

    update_record_selection(request)

    templates = dict(l='list')

    viewmode = request.GET.get('v', 'thumb')
    if viewmode == 'l':
        pagesize = max(min(safe_int(request.GET.get('ps', '100'), 100), 200), 5)
    else:
        pagesize = max(min(safe_int(request.GET.get('ps', '50'), 50), 100), 5)
    page = safe_int(request.GET.get('p', '1'), 1)
    sort = request.GET.get('s', 'score desc').lower()
    if not sort.endswith(" asc") and not sort.endswith(" desc"): sort += " asc"
    criteria = request.GET.getlist('c')
    orquery = request.GET.get('or', None)
    remove = request.GET.get('rem', None)
    if remove: criteria.remove(remove)
    keywords = request.GET.get('kw', '')

    if request.GET.has_key('action'):
        page = safe_int(request.GET.get('op', '1'), 1)

    if selected:
        selected = request.session.get('selected_records', ())

    available_storage = accessible_ids_list(request.user, Storage)

    exclude_facets = ['identifier']

    fields = Field.objects.filter(standard__prefix='dc').exclude(name__in=exclude_facets)

    search_facets = [SearchFacet('tag', 'Tags')] + [SearchFacet(field.name + '_t', field.label) for field in fields]
    search_facets.append(StorageSearchFacet('resolution', 'Image size', available_storage))
    search_facets.append(StorageSearchFacet('mimetype', 'Media type', available_storage))
    search_facets.append(CollectionSearchFacet('collections', 'Collection'))
    # convert to dictionary
    search_facets = dict((f.name, f) for f in search_facets)

    query = _generate_query(search_facets, request.user, collection, criteria, keywords, selected, remove)

    s = SolrIndex()

    return_facets = search_facets.keys()

    (hits, records, facets) = s.search(query, sort=sort, rows=pagesize, start=(page - 1) * pagesize,
                                       facets=return_facets, facet_mincount=1, facet_limit=100)

    tn = {}
    for record in records:
        url = record.get_thumbnail_url()
        t = get_thumbnail_for_record(record)
        tn[record.id] = {"t.id": t.id, "t.name": t.name, "t.url": url, "t.mimetype": t.mimetype,
                         "record_id": record.id, "record_name": record.name}
    json = {"records" : serializers.serialize("json",records),
            "thumbnails" : simplejson.dumps(tn)}
    return HttpResponse(simplejson.dumps(json), content_type='application/javascript')

def record(request, id, name):
    record = Record.objects.filter(id=id,
             collection__id__in=accessible_ids(request.user, Collection)).distinct()
    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))

    fieldsets = FieldSet.objects.filter(Q(owner=request.user) | Q(standard=True)).order_by('title')

    selected_fieldset = request.GET.get('fieldset')
    if selected_fieldset == '_all':
        fieldset = None
    elif selected_fieldset:
        f = fieldsets.filter(name=selected_fieldset)
        if f:
            fieldset = f[0]
        else:
            fieldset = record.fieldset
            selected_fieldset = None
    else:
        fieldset = record.get(id=id).fieldset

    fieldvalues = record.get(id=id).get_fieldvalues(fieldset=fieldset)

    dict =  {'record': serializers.serialize("json", record),
             'media': serializers.serialize("json", media),
             'fieldsets': serializers.serialize("json", fieldsets),
             #'selected_fieldset': serializers.serialize("json", simplejson.dumps(fieldset)),
             'fieldvalues': serializers.serialize("json", fieldvalues)
             }

    return HttpResponse(simplejson.dumps(dict), content_type='application/javascript')

def _generate_query(search_facets, user, collection, criteria, keywords, selected, *exclude):

    fields = {}
    for c in criteria:
        if c in exclude:
            continue
        (f, o) = c.split(':', 1)
        if f.startswith('-'):
            f = 'NOT ' + f[1:]
        fname = f.rsplit(' ',1)[-1]

        # create exact match criteria on the fly if needed
        if fname.endswith('_s') and not search_facets.has_key(fname):
            search_facets[fname] = ExactValueSearchFacet(fname)

        o = search_facets[fname].process_criteria(o, user)
        fields.setdefault(f, []).append('(' + o.replace('|', ' OR ') + ')')
    fields = map(lambda (name, crit): '%s:(%s)' % (name, (name.startswith('NOT ') and ' OR ' or ' AND ').join(crit)),
                 fields.iteritems())

    def build_keywords(q, k):
        k = k.lower()
        if k == 'and' or k == 'or':
            return q + ' ' + k.upper()
        elif q.endswith(' AND') or q.endswith(' OR'):
            return q + ' ' + k
        else:
            return q + ' AND ' + k

    if keywords: keywords = reduce(build_keywords, keywords.split())

    query = ''
    if fields:
        query = ' AND '.join(fields)
    if keywords:
        query = query and '%s AND (%s)' % (query, keywords) or '(%s)' % keywords
    if not query:
        query = '*:*'
    if collection:
        query = 'collections:%s AND %s' % (collection.id, query)
    if selected:
        query = 'id:(%s) AND %s' % (' '.join(map(str, selected)), query)

    if not user.is_superuser:
        groups = ' '.join(map(str, accessible_ids_list(user, Collection)))
        c = []
        if groups: c.append('collections:(%s)' % groups)
        if user.id: c.append('owner:%s' % user.id)
        if c:
            query = '(%s) AND %s' % (' OR '.join(c), query)
        else:
            query = 'id:"-1"'

    return query


@json_view
def presentations_for_current_user(request):
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
                content=[
                    dict(
                        id=item.record.id,
                        name=item.record.name,
                        title=item.record.title,
                        thumbnail=item.record.get_thumbnail_url(),
                        metadata=[
                            dict(
                                label=value.resolved_label,
                                value=value.value
                                )
                            for value in item.record.get_fieldvalues(owner=request.user, context=p)
                        ]
                    )
                    for item in p.items.select_related('record')
                ]
                 )
