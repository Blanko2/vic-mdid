from django.db.models import Count
from django.core.cache import cache
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.utils.http import urlquote
from django import forms
from django.forms.formsets import formset_factory
from django.db.models import Q
from django.contrib.auth.models import User
from . import SolrIndex
from rooibos.access import filter_by_access, accessible_ids, accessible_ids_list
from rooibos.util import safe_int, json_view
from rooibos.data.models import Field, Collection, FieldValue
from rooibos.storage.models import Storage
from rooibos.ui import update_record_selection, clean_record_selection_vars
import re
import copy
import random
from rooibos.flickr.models import FlickrSearch


class SearchFacet(object):
    
    def __init__(self, name, label):
        self.name = name
        self.label = label
        
    def process_criteria(self, criteria, *args, **kwargs):
        return criteria
        
    def set_result(self, facets):
        # break down dicts into tuples
        if hasattr(facets, 'items'):
            self.facets = facets.items()
        else:
            self.facets = facets
            
    def clean_result(self, hits):
        # sort facet items and remove the ones that match all hits
        self.facets = filter(lambda f: f[1] < hits, self.facets)
        self.facets = sorted(self.facets, key=lambda f: len(f) > 2 and f[2] or f[0])
        
    def or_available(self):
        return True
    
    def display_value(self, value):
        return value.replace('|', ' or ')


class OwnerSearchFacet(SearchFacet):
    
    def display_value(self, value):
        value = '|'.join(User.objects.filter(id__in=value.split('|')).values_list('username', flat=True))
        return super(OwnerSearchFacet, self).display_value(value)
    
    def set_result(self, facets):
        self.facets = ()
        

class StorageSearchFacet(SearchFacet):

    _storage_facet_re = re.compile(r'^s(\d+)-(.+)$')
   
    def __init__(self, name, label, available_storage):
        super(StorageSearchFacet, self).__init__(name, label)
        self.available_storage = available_storage
 
    def process_criteria(self, criteria, user, *args, **kwargs):
        criteria = '|'.join('s*-%s' %s for s in criteria.split('|'))
        return user.is_superuser and criteria \
            or '(%s) AND (%s)' % (' '.join('s%s-*' % s for s in self.available_storage), criteria)

    def set_result(self, facets):
        result = {}
        if facets:
            for f in facets.keys():
                m = StorageSearchFacet._storage_facet_re.match(f)
                if m and int(m.group(1)) in self.available_storage:
                    result[m.group(2)] = None  # make facet available, but without frequency count            
        super(StorageSearchFacet, self).set_result(result)


class CollectionSearchFacet(SearchFacet):
    
    def set_result(self, facets):
        result = []
        for id, title in Collection.objects.filter(id__in=map(int, facets.keys())).values_list('id', 'title'):
            result.append((id, facets[str(id)], title))
        super(CollectionSearchFacet, self).set_result(result)

    def display_value(self, value):
        value = '|'.join(Collection.objects.filter(id__in=value.split('|')).values_list('title', flat=True))
        return super(CollectionSearchFacet, self).display_value(value)


class ExactValueSearchFacet(SearchFacet):
    
    _special = re.compile(r'(\+|-|&&|\|\||!|\(|\)|\{|}|\[|\]|\^|"|~|\*|\?|:|\\)')
    
    def __init__(self, name):
        prefix, name = ([None] + name[:-2].split('.'))[-2:]
        if prefix:
            field = Field.objects.get(standard__prefix=prefix, name=name)
        else:
            field = Field.objects.get(standard=None, name=name)
        super(ExactValueSearchFacet, self).__init__(name, field.label)
    
    def process_criteria(self, criteria, *args, **kwargs):
        return '"' + self._special.sub(r'\\\1', criteria) + '"'

    def or_available(self):
        return False


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


def selected(request):
    return search(request, selected=True)

def search(request, id=None, name=None, selected=False, json=False):
    collection = id and get_object_or_404(filter_by_access(request.user, Collection), id=id) or None
    
    update_record_selection(request)
    
    templates = dict(l='list', im='images')
    
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
    
    search = FlickrSearch()
    results = search.photoSearch(keywords)
    flickr_total = results['total']
    
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
    search_facets.append(OwnerSearchFacet('owner', 'Owner'))
    # convert to dictionary
    search_facets = dict((f.name, f) for f in search_facets)

    query = _generate_query(search_facets, request.user, collection, criteria, keywords, selected, remove)
       
    s = SolrIndex()
    
    if json:
        return_facets = []
    else:
        return_facets = search_facets.keys()
    
    (hits, records, facets) = s.search(query, sort=sort, rows=pagesize, start=(page - 1) * pagesize,
                                       facets=return_facets, facet_mincount=1, facet_limit=100)

    if json:
        return render_to_string('results_bare_' + templates.get(viewmode, 'icons') + '.html',
                              {'records': records,
                               'selectable': True,},
                              context_instance=RequestContext(request))

    for f in search_facets:
        search_facets[f].set_result(facets.get(f))
    
    orfacet = None
    if orquery:
        (f, v) = orquery.split(':', 1)
        orfacets = s.search(_generate_query(search_facets, request.user, collection, criteria, keywords, selected,
                                            remove, orquery),
                            rows=0, facets=[f], facet_mincount=1, facet_limit=100)[2]
        orfacet = copy.copy(search_facets[f])
        orfacet.label = '%s in %s or...' % (v.replace("|", " or "), orfacet.label)
        orfacet.set_result(orfacets[f])
    
    if collection:
        url = reverse('solr-search-collection', kwargs={'id': collection.id, 'name': collection.name})
    elif selected:
        url = reverse('solr-selected')
    else:
        url = reverse('solr-search')
    
    q = request.GET.copy()
    q = clean_record_selection_vars(q)
    q.pop('or', None)
    q.pop('rem', None)
    q.pop('action', None)
    q.pop('p', None)
    q.pop('op', None)
    q.setlist('c', criteria)
    hiddenfields = [('op', page)]
    for f in q:
        if f != 'kw':
            for l in q.getlist(f):
                hiddenfields.append((f, l))
    qurl = q.urlencode()
    q.setlist('c', filter(lambda c: c != orquery, criteria))
    qurl_orquery = q.urlencode()    
    limit_url = "%s?%s%s" % (url, qurl, qurl and '&' or '')
    limit_url_orquery = "%s?%s%s" % (url, qurl_orquery, qurl_orquery and '&' or '')
    prev_page_url = None
    next_page_url = None
    
    if page > 1:
        q['p'] = page - 1
        prev_page_url = "%s?%s" % (url, q.urlencode())
    if page < (hits - 1) / pagesize + 1:
        q['p'] = page + 1
        next_page_url = "%s?%s" % (url, q.urlencode())

    q.pop('s', None)
    form_url = "%s?%s" % (url, q.urlencode())

    def readable_criteria(c):
        (f, o) = c.split(':', 1)        
        if f.startswith('-'):
            return (c, '%s not in %s' % (search_facets[f[1:]].display_value(o),
                                         search_facets[f[1:]].label), False)
        else:
            return (c, '%s in %s' % (search_facets[f].display_value(o),
                                     search_facets[f].label), search_facets[f].or_available())

    
    # sort facets by label
    facets = sorted(search_facets.values(), key=lambda f: f.label)
    
    # clean facet items
    for f in facets:
        f.clean_result(hits)
    
    # remove facets with only no filter options
    facets = filter(lambda f: len(f.facets) > 0, facets)    

    sort = sort.startswith('random') and 'random' or sort.split()[0]
    sort = sort.endswith('_sort') and sort[:-5] or sort

    return render_to_response('results.html',
                              {'criteria': map(readable_criteria, criteria),
                               'query': query,
                               'keywords': keywords,
                               'hiddenfields': hiddenfields,
                               'records': records,
                               'hits': hits,
                               'page': page,
                               'pages': (hits - 1) / pagesize + 1,
                               'prev_page': prev_page_url,
                               'next_page': next_page_url,
                               'reset_url': url,
                               'form_url': form_url,
                               'limit_url': limit_url,
                               'limit_url_orquery': limit_url_orquery,
                               'facets': facets,
                               'orfacet': orfacet,
                               'orquery': orquery,
                               'sort': sort,
                               'sortfields': fields,
                               'random': random.random(),
                               'viewmode': viewmode,
                               'flickr_total': flickr_total,},
                              context_instance=RequestContext(request))


@json_view
def search_json(request, id=None, name=None, selected=False):
    return dict(html=search(request, id, name, selected, json=True))
    

def browse(request, id=None, name=None):
    collections = filter_by_access(request.user, Collection) \
        .annotate(num_records=Count('records')).filter(num_records__gt=0).order_by('title')
    if not collections:
        raise Http404()
    if request.GET.has_key('c'):
        collection = get_object_or_404(collections, name=request.GET['c'])
        return HttpResponseRedirect(reverse('solr-browse-collection',
                                            kwargs={'id': collection.id, 'name': collection.name}))
    
    collection = id and get_object_or_404(collections, id=id) or collections[0]

    fields = cache.get('browse_fields_%s' % collection.id)
    if fields:
        fields = list(Field.objects.filter(id__in=fields))
    else:
        fields = list(Field.objects.filter(fieldvalue__record__collection=collection).distinct())
        cache.set('browse_fields_%s' % collection.id, [f.id for f in fields], 60)        
    
    if not fields:
        raise Http404()
    
    if request.GET.has_key('f'):
        field = get_object_or_404(Field, name=request.GET['f'], id__in=(f.id for f in fields))
    else:
        field = fields[0]
        
    values = FieldValue.objects.filter(field=field, record__collection=collection).values('value').annotate(freq=Count('value', distinct=False)).order_by('value')
    
    if request.GET.has_key('s'):
        start = values.filter(value__lt=request.GET['s']).count() / 50 + 1
        return HttpResponseRedirect(reverse('solr-browse-collection',
                                            kwargs={'id': collection.id, 'name': collection.name}) +
                                    "?f=%s&page=%s" % (field.name, start))
    
    return render_to_response('browse.html',
                              {'collections': collections,
                               'selected_collection': collection and collection or None,
                               'fields': fields,
                               'selected_field': field,
                               'values': values,},
                              context_instance=RequestContext(request))


def overview(request):
    
    collections = filter_by_access(request.user, Collection).order_by('title').annotate(num_records=Count('records'))
    
    return render_to_response('overview.html',
                              {'collections': collections,},
                              context_instance=RequestContext(request))
    
    
def fieldvalue_autocomplete(request):
    collection_ids = request.GET.get('collections')
    q = collection_ids and Collection.objects.filter(id__in=collection_ids.split(',')) or Collection
    collections = filter_by_access(request.user, q)
    if not collections:
        raise Http404()
    query = request.GET.get('q', '').lower()
    limit = min(int(request.GET.get('limit', '10')), 100)    
    field = request.GET.get('field')
    q = field and Q(field__id=field) or Q()
    values = FieldValue.objects.filter(q, record__collection__in=collections, value__icontains=query) \
        .values_list('value', flat=True).distinct().order_by('value')[:limit]
    values = '\n'.join(urlquote(v) for v in values)
    return HttpResponse(content=values)


def search_form(request):
    
    collections = filter_by_access(request.user, Collection)
    if not collections:
        raise Http404()

    def _get_fields():
        return Field.objects.select_related('standard').all().order_by('standard__title', 'name')
    
    def _cmp(x, y):
        if x == "Other": return 1
        if y == "Other": return -1
        return cmp(x, y)
    
    def _field_choices():        
        grouped = {}
        for f in _get_fields():
            grouped.setdefault(f.standard and f.standard.title or 'Other', []).append(f)
        return [('', 'Any')] + [(g, [(f.id, f.label) for f in grouped[g]]) for g in sorted(grouped, _cmp)]

    class SearchForm(forms.Form):
        TYPE_CHOICES = (('t', 'in'), ('T', 'not in'))
        criteria = forms.CharField(required=False)        
        type = forms.ChoiceField(choices=TYPE_CHOICES, required=False, label='')
        field = forms.ChoiceField(choices=_field_choices(), required=False, label='')
        
    def _collection_choices():
        result = []
        for c in collections:
            title = c.title
            children = c.all_child_collections
            if children:
                title += " (including %s sub-collections)" % len(children)
            result.append((c.id, title))
        return result
        
    class CollectionForm(forms.Form):
        collections = forms.MultipleChoiceField(choices=_collection_choices(),
                                                widget=forms.CheckboxSelectMultiple,
                                                required=False)
        
    SearchFormFormSet = formset_factory(form=SearchForm, extra=5)
    
    if request.method == "POST":
        collectionform = CollectionForm(request.POST, prefix='coll')
        formset = SearchFormFormSet(request.POST, prefix='crit')        
        if formset.is_valid() and collectionform.is_valid():
            core_fields = dict((f, f.get_equivalent_fields()) for f in Field.objects.filter(standard__prefix='dc'))
            query = []
            keywords = []
            for form in formset.forms:
                field = form.cleaned_data['field']
                type = form.cleaned_data['type']
                criteria = form.cleaned_data['criteria']
                if criteria:
                    if field:
                        field = Field.objects.get(id=field)                        
                        for cf, cfe in core_fields.iteritems():
                            if field == cf or field in cfe:
                                field = cf
                                break
                        query.append('c=%s%s_%s:%s' % (type.isupper() and '-' or '', field.name, type.lower(), urlquote(criteria)))
                    else:
                        keywords.append('%s"%s"' % (type.isupper() and '-' or '', urlquote(criteria)))
            collections = collectionform.cleaned_data['collections']
            if collections:
                query.append('c=collections:%s' % '|'.join(collections))
            if query or keywords:
                qs = 'kw=%s&' % '+'.join(keywords) + '&'.join(query)
                return HttpResponseRedirect(reverse('solr-search') + '?' + qs)
    else:
        collectionform = CollectionForm(prefix='coll')
        formset = SearchFormFormSet(prefix='crit')
    
    return render_to_response('search.html',
                              {'collectionform': collectionform,
                               'formset': formset,
                               },
                              context_instance=RequestContext(request))