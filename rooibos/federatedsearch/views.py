from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from rooibos.util import json_view
from datetime import datetime, timedelta
from threading import Thread
from models import HitCount

from nasa import NasaImageExchange
from artstor import ArtstorSearch
from flickr import FlickrSearch
from dummy import Dummy
from rooibos.unitedsearch import aggregate

import logging
import re
import json


#sources = {
#    'NasaImageExchange': NasaImageExchange,
#    'ArtstorSearch': ArtstorSearch,
#    'Flickr': FlickrSearch,
#}

source_classes = [
    NasaImageExchange,
    ArtstorSearch,
    FlickrSearch,
] + aggregate.federatedSearchSources()


def sidebar_api_raw(request, query, params={}, cached_only=False):


    print "\n\nQUERY:"
    print query
    print "\n\nPARAMS:"
    print params
    print "\n\n"
    sources = dict(
        (lambda s: (s.get_source_id(), s))(c()) for c in source_classes
    )

    if not request.user.is_authenticated():
        return dict(html="Please log in to see additional content.", hits=0)

    if not query:
        return dict(html='Please specify at least one search criteria to find additional content.', hits=0)

    cache = dict(HitCount.current_objects.filter(query=query, source__in=sources.keys()).values_list('source','hits'))

    class HitCountThread(Thread):
        def __init__(self, source):
            super(HitCountThread, self).__init__()
            self.source = source
            self.hits = 0
            self.instance = None
            self.cache_hit = False
        def run(self):
            self.instance = sources[self.source]
            # if we've done this search before, simply use the cached result, don't bother re-searching
            if cache.has_key(self.source):
                self.cache_hit = True
                if cache[self.source]:
                    self.hits = cache[self.source]
            elif not cached_only:
                try:
                    self.hits = self.instance.hits_count(query, params=params)
                    HitCount.objects.create(query=query,
                                            source=self.source,
                                            hits=self.hits,
                                            valid_until=datetime.now() + timedelta(1))
                except Exception, e:
                    import traceback
                    logging.error("Federated Search: %s\n%s" % (e, traceback.format_exc()))
                    self.hits = -1


    threads = []
    for source in sorted(sources.keys()):
        thread = HitCountThread(source)
        threads.append(thread)
        thread.start()

    results = []
    total_hits = 0
    cache_hit = True
    for thread in threads:
        thread.join()
        cache_hit = cache_hit and thread.cache_hit
        if thread.hits:
            if thread.hits > 0:
                total_hits += thread.hits
            results.append((thread.instance, thread.hits))

    return dict(html=render_to_string('federatedsearch_results.html',
                            dict(results=sorted(results),
                                 query=query,
                                 params=params),
                            context_instance=RequestContext(request)),
                hits=total_hits,
                cache_hit=cache_hit)

@json_view
def sidebar_api(request):
    query = ' '.join(request.GET.get('q', '').strip().lower().split())
 
    # build params from query if possible (if query contains type=value parameters)
    subquery = query.split('keywords=')[1]
    params={}
    keywords=""
    # trim 'search=search_type, keywords='
    clauses = subquery.split(',')

    for clause in clauses:
	    type_value = clause.strip().split("=", 1)
	    if len(type_value) == 1:
		    keywords += type_value[0] + " "
	    elif len(type_value) > 1:
                params[type_value[0]]= type_value[1]
    
    query = re.sub("(?<=keywords=).*", keywords.strip(), query) + ", params=" + json.dumps(params)
    return sidebar_api_raw(request, query, params)
