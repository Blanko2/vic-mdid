from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from models import SolrIndex
from rooibos.util.util import safe_int
from rooibos.data.models import Field

def search(request):

    pagesize = max(min(safe_int(request.GET.get('ps', '50'), 50), 100), 10)
    page = safe_int(request.GET.get('p', '1'), 1)
    query = request.GET.get('q')
    sort = request.GET.get('s', 'score')
    limit = request.GET.get('l')
    
    if limit:
        if query:
            query = '%s AND (%s)' % (limit, query)
        else:
            query = limit

    q = request.GET.copy()
    if query:
        q['q'] = query
    else:
        query = '*:*'        
    
    fields = ['country_t','creator_t','material_t','style_t','period_t']
    
    s = SolrIndex()
    (hits, records, facets) = s.search(query, rows=pagesize, start=(page - 1) * pagesize, facets=fields, facet_mincount=1, facet_limit=50)

    if hits and not records:
        page = (hits - 1) / pagesize + 1
        (hits, records, facets) = s.search(query, rows=pagesize, start=(page - 1) * pagesize, facets=fields, facet_mincount=1, facet_limit=50)

    if limit:
        del(q['l'])
    
    qurl = q.urlencode()
    limit_url = "%s?%s%sl=" % (reverse('solr-search'), qurl, qurl and '&' or '')
    prev_page_url = None
    next_page_url = None
    
    if page > 1:
        q['p'] = page - 1
        prev_page_url = "%s?%s" % (reverse('solr-search'), q.urlencode())
    if page < (hits - 1) / pagesize + 1:
        q['p'] = page + 1
        next_page_url = "%s?%s" % (reverse('solr-search'), q.urlencode())

    for f in facets:
        facets[f] = sorted(facets[f].iteritems())
    facets = sorted(facets.iteritems())

    return render_to_response('results.html',
                              {'query': query,
                               'records': records,
                               'hits': hits,
                               'page': page,
                               'pages': (hits - 1) / pagesize + 1,
                               'prev_page': prev_page_url,
                               'next_page': next_page_url,
                               'limit_url': limit_url,
                               'facets': facets},
                              context_instance=RequestContext(request))
