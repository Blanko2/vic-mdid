from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from . import NasaImageExchange

def search(request):
    
        query = request.GET.get('q')
        n = NasaImageExchange()
        records = n.search(query)
    
        return render_to_response('nasa-nix-results.html',
                              {'query': query,
                               'records': records,
                               'hits': records and len(records) or 0},
                              context_instance=RequestContext(request))
