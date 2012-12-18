from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect
from rooibos.userprofile.views import load_settings, store_settings
from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.util.models import OwnedWrapper
from presentation.models import Presentation
from django.db.models import Q
from rooibos.access import filter_by_access
from django.db import backend
from django.contrib.auth.models import User
from django.db.models.aggregates import Count
import json

from rooibos.unitedsearch import searchers,external
from rooibos.unitedsearch.union import searcherUnion

import rooibos.unitedsearch.views 

from urllib import urlencode

@csrf_protect
def m_main(request):
    #form = AuthenticationForm()
    request.session.set_test_cookie()
    return render_to_response('mobileHome.html', {'defaultDatabase':'nga'}, context_instance=RequestContext(request))

    
def m_search_redirect(request):
  db = request.GET.get("database")
  searchTerm = request.GET.get("q")
  offset = request.GET.get("from")
  return HttpResponseRedirect(reverse('mobile-search', kwargs={'database':db})+"?"+urlencode({'q':searchTerm})+"&from="+offset)
    
    

searchersmap = dict([(s.identifier, s) for s in searchers.all])
classList = ['ui-block-a', 'ui-block-b', 'ui-block-c', 'ui-block-d']  

def grid_classify_3(item, index):
  return {'item':item, 'class':classList[index%3]}
  
def grid_classify_4(item, index):
  return {'item':item, 'class':classList[index%4]}

  
  

def m_search(request, database):
	
	searcherNodes = [s.identifier for s in searchers.all]
	indices = [i for i in range(len(searcherNodes))]
	searcherNodes = map(grid_classify_3, searcherNodes, indices)
		
	searchTerm = request.GET.get("q")
	offset = int(request.GET.get("from"))
	
	dbSearcher = usViewer(searchersmap[database])
	results = dbSearcher.search(request)
	
	def strip_ident(dic):
	  del dic["identifier"]
	
	map(strip_ident, results["results"])
	jsonStrings = map(json.dumps, results["results"])
	
	for i in range(len(results["results"])):
	  results["results"][i]["json"] = jsonStrings[i]
	
	indices = [i for i in range(len(results))]
	resultsObjects = map(grid_classify_3, results['results'], indices)

	return render_to_response('mobileSearch.html', {'searchDatabase':database, 'databases':searcherNodes, 'searchTerm':searchTerm, 'results':resultsObjects, 'offset':str(offset), 'nextPage':str(offset+6), 'lastPage':str((offset-6) if (offset-6) >= 0 else 0)})   

def m_showImage(request):
	#imageData = json.loads()
	jsonData = request.POST.get('jsonOutput')
	print jsonData
	jsonData = json.loads(jsonData)
	return render_to_response('imageViewer.html', {'imageData':jsonData})

def m_presentation(request, course, lecture):
	return HttpResponse("Hello, course is:"+course+" lecture is:"+lecture)

def m_presentationList(request):
	
	class ACourse():
		courseName = ""
		contents = []

	courses = []
	for i in range(1,6):
		c = ACourse()
		c.courseName = "ARTH10"+str(i)
		c.contents = []

		for j in range(3):
			c.contents.append("lecture"+str(j))

		courses.append(c)

	return render_to_response('mobilePresentationList.html', {'courses':courses})


class usViewer(rooibos.unitedsearch.views.usViewer):
    def __init__(self, searcher):
        self.searcher = searcher
        rooibos.unitedsearch.views.usViewer.__init__(self, searcher, None)

    def search(self, request):
      return self.perform_search(request,6)  
        
    def url_select(self):
        return reverse("mobile-search", kwargs={"database": self.searcher.identifier})

    def url_search(self):
        return reverse("mobile-search", kwargs={"database": self.searcher.identifier})
    
class usUnionViewer(usViewer):
    def __init__(self, searcher):
        usViewer.__init__(self, searcher)

    def url_search(self):
        return reverse("mobile-union-search", kwargs={"sid": self.searcher.identifier})


def union(request, sid):
    from unitedsearch.union import searcherUnion
    slist = map(searchersmap.get, sid.split(","))
    searcher = slist[0] if len(slist) == 1 else searcherUnion(slist)
    return usUnionViewer(searcher)

def union_search(request, sid="local"):
    return union(request, sid).search(request)

    
"""def m_search(request):
   viewer = usViewer(searcherUnion([external.digitalnz,external.flickr]))
   return viewer.search(request)
"""

def redirect(request):
    searchterm = request.GET.get('q')
    return HttpResponseRedirect(reverse("mobile-union-search",kwargs={'sid':"gallica"}) + "?" + urlencode({'q': searchterm}))

def m_browse(request, manage=False):

    presenter = request.GET.get('presenter')
    
    tags = ["ARTH101", "ARTH102", "ARTH243"]

    qs = OwnedWrapper.objects.filter(content_type=OwnedWrapper.t(Presentation))
    # get list of matching IDs for each individual tag, since tags may be attached by different owners
    ids = [list(TaggedItem.objects.get_by_model(qs, '"%s"' % tag).values_list('object_id', flat=True)) for tag in tags]
    
    
    q = []
    for x in ids:
      q.append(Q(id__in=x))
      
        
    pOut = []
    presentations = filter_by_access(request.user, Presentation )
    
    i = 0
    for x in q:
      pOut.append( list(presentations.select_related('owner').filter(x).order_by('title')) )
      i+=1
          
    class ACourse():
	courseName = ""
	contents = []
    
    def courseify(name, presentations):
      c = ACourse()
      c.courseName = name
      c.contents = presentations
      return c
    
    courses = map(courseify, tags, pOut)
    
    

    return render_to_response('mobilePresentationList.html',
                          { 'courses': courses },
                          context_instance=RequestContext(request))
        

