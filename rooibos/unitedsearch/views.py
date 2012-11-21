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

	def htmlparams(self, defaults):
		def out(params, indent, prefix, default):
			label = params.label if params.label else " ".join(prefix)
			if isinstance(params, MapParameter):
				r = ["  "*indent + "<div>"]
				for index in range(len(params.parammap)-1, -1, -1) :
				#for k in params.parammap:
					k = params.parammap.keys()[index]
					r += out(params.parammap[k], indent + 1, prefix + [k], default != None and default[k] != None and default[k])
				r += ["  "*indent + "</div>"]
				return r
			elif isinstance(params, ScalarParameter):
				return ["  "*indent + (label + ": " if params.label else "") + "<input type=\"text\" name=\"i_" + "_".join(prefix) + "\" value=\"" + (default or "") + "\" />"]
			elif isinstance(params, OptionalParameter):
				r = ["  "*indent + "<div>"]
				indent += 1
				r += ["  "*indent + "<input name=\"i_" + "_".join(prefix) + "\" type=\"checkbox\" class=\"param-opt-a\"" + (" checked=\"true\"" if default else "") + "> " + label]
				r += ["  "*indent + "<div class=\"param-opt\">"]
				r += out(params.subparam, indent + 1, prefix + ["opt"], default and default[0] or None)
				r += ["  "*indent + "</div>"]
				indent -= 1
				r += ["  "*indent + "</div>"]
				return r
			elif isinstance(params, DefinedListParameter):
				options = params.options or []
				r_content = "  "*indent + (label + ": " if params.label else "") 
				#r_content += "<select name=\"i_" + "_".join(prefix) + "\"" + ("" or default and " value=\"" + default + "\"") + ">"
				r_content += "<select name=\"i_" + "_".join(prefix) + "\""
				if params.multipleAllowed :
				  r_content += " multiple = \"multiple\""
				r_content += ">"
				selected_option = default or options[0]
				for option in options :
				    r_content += "<option value=" + option
				    if option == selected_option :
				      r_content += " selected=\"selected\""
				    r_content += ">" + option + "</option>"
				r_content += "</select>"
				return [r_content]
			elif isinstance(params, UserDefinedTypeParameter) :
			      options = params.type_options or []
			      r_content = "  "*indent + (label + ": " if params.label else "")
			      
			      r_content += "<div>"
			      
			      # select box for the type options
			      r_content += "<select name=\"i_" + "_".join(prefix) +"_type"+ "\">"
			      for option in options :
				    r_content += "<option value=" + option
				    r_content += ">" + option + "</option>"
			      r_content += "</select><br>"
			      
			      # textbox for value
			      if default and len(default) >0:
				value = default[1]
			      else:
				value = ""
			      r_content += "<input name=\"i_" + "_".join(prefix)+"_value" + "\" type=\"text\" value=\"" + value + "\" />"
			      
			      r_content += "</div>"
			      
			      return [r_content]
			    
		return "\n".join(out(self.searcher.parameters, 0, [], defaults))

	
	def readargs(self, getdata):
		inputs = dict([(n[2:], getdata[n]) for n in getdata if n[:2] == "i_"])
		def read(params, prefix):
			if isinstance(params, MapParameter):
				r = {}
				for k in params.parammap:
					if k in r :
					  r[k].append(read(params.parammap[k], prefix + [k]))
					else :
					  r[k] = read(params.parammap[k], prefix + [k])
				return r
			if isinstance(params, ScalarParameter):
				if "_".join(prefix) in inputs:
					return inputs["_".join(prefix)]
			if isinstance(params, OptionalParameter):
				return [read(params.subparam, prefix + ["opt"])] if inputs.get("_".join(prefix), "off") == "on" else []
			if isinstance(params, DefinedListParameter):
				if "_".join(prefix) in inputs:
					return inputs["_".join(prefix)]

			if isinstance(params, UserDefinedTypeParameter) :
				field_type = ""
				field_value = ""
				if "_".join(prefix)+"_type" in inputs:
					field_type = inputs["_".join(prefix)+"_type"]
				if "_".join(prefix)+"_value" in inputs:
					field_value = inputs["_".join(prefix)+"_value"]
				return [field_type, field_value]
				#if "_".join(prefix) in inputs:
				#	return inputs["_".join(prefix)]
		return read(self.searcher.parameters, [])
	
	def perform_search(self, request, resultcount):
		query = request.GET.get('q', '') or request.POST.get('q', '')
		offset = request.GET.get('from', '') or request.POST.get('from', '') or "0"
		params = {}
		for n in request.GET:
			if n[:2] == "p-":
				params[n[2:]] = request.GET[n]
		#args = self.readargs(request.GET)
		result,args = self.searcher.search(query, {}, offset, resultcount)
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

		prev_off = hasattr(self.searcher, "previousOffset") and self.searcher.previousOffset(offset, resultcount)

		return {
				'results': map(resultpart, results),
				'select_url': self.url_select(),
				'next_page': self.__url_search_({ 'q': query, 'from': result.nextoffset }) if result.nextoffset else None,
				'previous_page': self.__url_search_({ 'q': query, 'from': prev_off }) if prev_off else None, 
				'hits': result.total,
				'searcher_name': self.searcher.name,
				'html_parameters': self.htmlparams(args)
			}
		
	def search(self, request):
		a = self.perform_search(request,50)
		print "previous_page: %s" % a["previous_page"]
		return render_to_response('searcher-results.html', a, context_instance=RequestContext(request))


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
