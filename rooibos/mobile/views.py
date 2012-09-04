from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect

from rooibos.unitedsearch import external
from urllib import urlencode

@csrf_protect
def m_main(request):
    print '** blah!!'
    form = AuthenticationForm()
    request.session.set_test_cookie()
    return render_to_response('m_login.html', {'form': form}, context_instance=RequestContext(request))

class usViewer():
    def __init__(self, searcher):
        self.searcher = searcher

    def search(self, request):
        query = request.GET.get('q', '') or request.POST.get('q', '')
        offset = int(request.GET.get('from', '') or request.POST.get('from', '') or 0)
        result = self.searcher.search(query, {}, offset, 6) # 50
        results = result.images
        return render_to_response('m_results.html',
            {
                'results': [ { 'thumb_url': i.thumb, 'title': i.name, 'record_url': i.infourl, 
                              'identifier': i.identifier } for i in results ],
                'select_url': reverse('united:%s:select' % self.searcher.identifier),
                'next_page': reverse('united:%s:search' % self.searcher.identifier) + "?" + urlencode({ 'q': query, 'from': result.nextoffset }),
                'hits': result.total,
                'searcher_name': self.searcher.name
            },
            context_instance=RequestContext(request))
        
def m_search(request):
    viewer = usViewer(external.flickr)
    return viewer.search(request)
        

