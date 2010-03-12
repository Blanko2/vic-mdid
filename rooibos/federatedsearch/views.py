from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from rooibos.util import json_view


@json_view
def sidebar_api(request):    
    return dict(html='No additional content found.', hits=0)
