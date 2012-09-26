from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from rooibos.workers.models import JobInfo
from django.template import RequestContext
from rooibos.ui.views import select_record
from django.utils import simplejson
from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from django.conf.urls.defaults import *
from urllib import urlencode
from common import *
from . import *
import searchers

import sys
import traceback

class usViewer():
	def __init__(self, searcher, mynamespace):
		self.urlpatterns = patterns('',
			url(r'^search/', self.search, name='search'),
			url(r'^select/', self.select, name='select'))
		self.searcher = searcher
		self.namespace = mynamespace
	
	def url_select(self):
		return reverse(self.namespace + ':select')
	
	def url_search(self):
		return reverse(self.namespace + ':search')
	
	def __url_search_(self, params={}):
		u = self.url_search()
		return u + (("&" if "?" in u else "?") + urlencode(params) if params else "")

	def htmlparams(self):
		def out(params, indent, prefix):
			label = params.label if params.label else " ".join(prefix)
			if isinstance(params, MapParameter):
				r = ["  "*indent + "<div>"]
				for k in params.parammap:
					r += out(params.parammap[k], indent + 1, prefix + [k])
				r += ["  "*indent + "</div>"]
				return r
			elif isinstance(params, ScalarParameter):
				return ["  "*indent + (label + ": " if params.label else "") + "<input type=\"text\" name=\"i_" + "_".join(prefix) + "\" value=\"\" />"]
			elif isinstance(params, OptionalParameter):
				r = ["  "*indent + "<a href=\"#\" class=\"param-opt-a\">" + label + "</a>", "  "*indent + "<div class=\"param-opt\">"]
				r += out(params.subparam, indent + 1, prefix + ["opt"])
				r += ["  "*indent + "</div>"]
				return r
		return "\n".join(out(self.searcher.parameters, 0, []))

	
	def readargs(self, getdata):
		inputs = dict([(n[2:], getdata[n]) for n in getdata if n[:2] == "i_"])
		def read(params, prefix):
			if isinstance(params, MapParameter):
				r = {}
				for k in params.parammap:
					r[k] = read(params.parammap[k], prefix + [k])
				return r
			if isinstance(params, ScalarParameter):
				if "_".join(prefix) in inputs:
					return inputs["_".join(prefix)]
			if isinstance(params, OptionalParameter):
				# TODO: this, properly
				return [read(params.subparam, prefix + ["opt"])]
		return read(self.searcher.parameters, [])
	
	def search(self, request):
		query = request.GET.get('q', '') or request.POST.get('q', '')
		offset = request.GET.get('from', '') or request.POST.get('from', '') or "0"
		params = {}
		for n in request.GET:
			if n[:2] == "p-":
				params[n[2:]] = request.GET[n]
		result = self.searcher.search(query, self.readargs(request.GET), offset, 50)
		results = result.images

		def resultpart(image):
			if isinstance(image, ResultRecord):
				return {
					"is_record": True,
					"thumb_url": image.record.get_thumbnail_url(),
					"title": image.record.title,
					"record_url": image.record.get_absolute_url(),
					"identifier": image.record.id
				}
			else:
				return {
					"thumb_url": image.thumb,
					"title": image.name,
					"record_url": image.infourl,
					"identifier": image.identifier
				}

		return render_to_response('searcher-results.html',
			{
				'results': map(resultpart, results),
				'select_url': self.url_select(),
				'next_page': self.__url_search_({ 'q': query, 'from': result.nextoffset }) if result.nextoffset else None,
				'hits': result.total,
				'searcher_name': self.searcher.name,
				'html_parameters': self.htmlparams()
			},
			context_instance=RequestContext(request))

	def record(self, identifier):
		image = self.searcher.getImage(identifier)
		if isinstance(image, ResultRecord):
			return image.record
		record = Record.objects.create(name=image.name,
						source=image.url,
						tmp_extthumb=image.thumb,
						manager='unitedsearch')

		def add_field(f, v, o):
			if type(v) == list:
				for w in v:
					add_field(f, w, o)
			elif v:
				# TODO: neaten?
				try:
					FieldValue.objects.create(
						record=record,
						field=standardfield(f),
						order=o,
						value=v)
				except:
					pass

		n = 0
		# go through the metadata given by the searcher; just add whatever can be added---what are not standard fields are simply skipped.
		for field, value in dict(image.meta, title=image.name).iteritems():
			add_field(field, value, n)
			n += 1

		collection = get_collection()
		CollectionItem.objects.create(collection=collection, record=record)
		job = JobInfo.objects.create(func='unitedsearch_download_media', arg=simplejson.dumps({
			'record': record.id,
			'url': image.url
		}))
		job.run()
		return record

	def select(self, request):
		if not request.user.is_authenticated():
			raise Http404()
		
		if request.method == "POST":
			# TODO: maybe drop the unused given-records portion of this
			imagesjs = simplejson.loads(request.POST.get('id', '[]'))
			images = map(self.searcher.getImage, imagesjs)
			urlmap = dict([(i.record.get_absolute_url() if isinstance(i, ResultRecord) else i.url, i) for i in images])
			urls = urlmap.keys()
			# map of relevant source URLs to record IDs that already exist
			ids = dict(Record.objects.filter(source__in=urls, manager='unitedsearch').values_list('source', 'id'))
			result = []
			for url in urls:
				id = ids.get(url)
				if id:
					result.append(id)
				else:
					i = urlmap[url].identifier
					record = self.record(i)
					result.append(record.id)
			r = request.POST.copy()
			r['id'] = simplejson.dumps(result)
			request.POST = r
		return select_record(request)

class usUnionViewer(usViewer):
	def __init__(self, searcher):
		usViewer.__init__(self, searcher, None)
	
	def url_select(self):
		return reverse("united:union-select", kwargs={"sid": self.searcher.identifier})

	def url_search(self):
		return reverse("united:union-search", kwargs={"sid": self.searcher.identifier})

searchersmap = dict([(s.identifier, s) for s in searchers.all])

def union(request, sid):
	from union import searcherUnion
	slist = map(searchersmap.get, sid.split(","))
	searcher = slist[0] if len(slist) == 1 else searcherUnion(slist)
	return usUnionViewer(searcher)

def union_select(request, sid="local"):
	return union(request, sid).select(request)

def union_search(request, sid="local"):
	return union(request, sid).search(request)
