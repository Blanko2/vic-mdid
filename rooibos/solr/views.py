from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from models import SolrIndex
from rooibos.util.util import safe_int

def search(request):

    pagesize = max(min(safe_int(request.GET.get('ps', '50'), 50), 100), 10)
    page = safe_int(request.GET.get('p', '1'), 1)
    query = request.GET.get('q', '*:*')
    sort = request.GET.get('s', 'score')
    
    s = SolrIndex()
    (hits, records) = s.search(query, rows=pagesize, start=(page - 1) * pagesize)

    if hits and not records:
        page = (hits - 1) / pagesize + 1
        (hits, records) = s.search(query, rows=pagesize, start=(page - 1) * pagesize)

    q = request.GET.copy()
    prev_page_url = None
    next_page_url = None
    
    if page > 1:
        q['p'] = page - 1
        prev_page_url = "%s?%s" % (reverse('solr-search'), q.urlencode())
    if page < (hits - 1) / pagesize + 1:
        q['p'] = page + 1
        next_page_url = "%s?%s" % (reverse('solr-search'), q.urlencode())


    return render_to_response('results.html',
                              {'query': query,
                               'records': records,
                               'hits': hits,
                               'page': page,
                               'pages': (hits - 1) / pagesize + 1,
                               'prev_page': prev_page_url,
                               'next_page': next_page_url, },
                              context_instance=RequestContext(request))
