from __future__ import with_statement
import os
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import get_object_or_404, render_to_response
from django.core.urlresolvers import reverse
from rooibos.access import filter_by_access
from rooibos.data.models import Collection
from . import PowerPointGenerator

def powerpoint_options(request, groupname):
    collection = get_object_or_404(filter_by_access(request.user, Collection), name=groupname) 
    template_urls = map(lambda t: reverse('powerpoint-generator', kwargs={'groupname': groupname, 'template': t}),
                        PowerPointGenerator.get_templates())
    return render_to_response('powerpoint_options.html',
                              {'template_urls': template_urls,
                               'collection': collection,},
                              context_instance=RequestContext(request))


def powerpoint_generator(request, groupname, template):
    collection = get_object_or_404(filter_by_access(request.user, Collection), name=groupname)        
    g = PowerPointGenerator(collection)
    filename = os.tempnam()
    try:
        g.generate(g.get_templates()[0], filename)
        with open(filename, mode="rb") as f:
            response = HttpResponse(content=f.read(),
                mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        response['Content-Disposition'] = 'attachment; filename=%s.pptx' % groupname
        return response        
    finally:
        os.unlink(filename)
