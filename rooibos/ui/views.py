from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse


def main(request):
    
    return render_to_response('main.html',
                              {},
                              context_instance=RequestContext(request))