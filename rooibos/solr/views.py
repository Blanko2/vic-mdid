from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from . import SolrIndex
from rooibos.access import filter_by_access, accessible_ids
from rooibos.util import safe_int
from rooibos.data.models import Field, Group
from rooibos.ui import update_record_selection, clean_record_selection_vars

def _generate_query(group, criteria, keywords, selected, *exclude):
    fields = {}
    for c in criteria:
        if c in exclude:
            continue
        (f, o) = c.split(':', 1)
        if f.startswith('-'):
            f = 'NOT ' + f[1:]        
        fields.setdefault(f, []).append('(' + o.replace('|', ' OR ') + ')')
    fields = map(lambda (name, crit): '%s:(%s)' % (name, (name.startswith('NOT ') and ' OR ' or ' AND ').join(crit)), fields.iteritems())
    
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
        query = query and '%s AND (%s)' % (query, keywords) or keywords
    if not query:
        query = '*:*'
    if group:
        query = 'groups:%s AND %s' % (group.id, query)
    if selected:
        query = 'id:(%s) AND %s' % (' '.join(map(str, selected)), query)
    return query

def selected(request):
    return search(request, selected=True)

def search(request, group=None, selected=False):
    if group:
        group = get_object_or_404(filter_by_access(request.user, Group), name=group)

    update_record_selection(request)
    
    pagesize = max(min(safe_int(request.GET.get('ps', '50'), 50), 100), 10)
    page = safe_int(request.GET.get('p', '1'), 1)
    sort = request.GET.get('s', 'score')
    criteria = request.GET.getlist('c')
    orquery = request.GET.get('or', None)
    remove = request.GET.get('rem', None)
    if remove: criteria.remove(remove)
    keywords = request.GET.get('kw', '')
    
    if request.GET.has_key('action'):
        page = safe_int(request.GET.get('op', '1'), 1)
    
    if selected:
        selected = request.session.get('selected_records', ())
    
    query = _generate_query(group, criteria, keywords, selected, remove)
    exclude_facets = ('date', 'identifier', 'relation', 'source')
    
    fields = Field.objects.filter(standard__prefix='dc').exclude(name__in=exclude_facets)
    fields = dict(map(lambda field: (field.name + '_t', field.label), fields))  
   
    s = SolrIndex()
    (hits, records, facets) = s.search(query, rows=pagesize, start=(page - 1) * pagesize, facets=fields.keys(), facet_mincount=1, facet_limit=50)
    
    if orquery:
        f = orquery.split(':', 1)[0]
        orfacets = s.search(_generate_query(group, criteria, keywords, selected, remove, orquery), rows=0, facets=[f], facet_mincount=1, facet_limit=50)[2]
    else:
        orfacets = None
    
    if group:
        url = reverse('solr-search-group', kwargs={'group': group.name})
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

    facets = sorted(
                map(lambda (name, items): {'name': name, 'items': sorted(items.iteritems()), 'label': fields[name]},
                    filter(lambda (name, items): len(items) > 1, facets.iteritems())),
                key=lambda f: f['label'])

    def readable_criteria(c):
        (f, o) = c.split(':', 1)
        o = o.replace('|', ' or ')
        if f.startswith('-'):
            return (c, '%s not in %s' % (o, fields[f[1:]]), False)
        else:
            return (c, '%s in %s' % (o, fields[f]), True)

    if orfacets:
        orfacets = map(lambda (name, items): {'name': name, 'items': sorted(items.iteritems()), 'label': readable_criteria(orquery)[1] + ' or ...'},
                        filter(lambda (name, items): len(items) > 1, orfacets.iteritems()))

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
                               'limit_url': limit_url,
                               'limit_url_orquery': limit_url_orquery,
                               'facets': facets,
                               'orfacets': orfacets,
                               'orquery': orquery,},
                              context_instance=RequestContext(request))
