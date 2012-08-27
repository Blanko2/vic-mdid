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
from common import *

import sys
import traceback

class usViewer():
	def __init__(self, searcher):
		self.urlpatterns = patterns('',
			url(r'^search/', self.search, name='search'),
			url(r'^select/', self.select, name='select'))
		self.searcher = searcher

	def search(self, request):
		query = request.GET.get('q', '') or request.POST.get('q', '')
		results = self.searcher.search(query, {}, 0, 50).images
		return render_to_response('searcher-results.html',
			{
				'results': [ { 'thumb_url': i.thumb, 'title': i.name, 'record_url': i.url, 'identifier': i.identifier } for i in results ],
				'select_url': reverse('united:%s:select' % self.searcher.identifier) },
			context_instance=RequestContext(request))

	def record(self, identifier):
		image = self.searcher.getImage(identifier)
		record = Record.objects.create(name=image.name,
						source=image.url,
						manager='unitedsearch')
		n = 0
		# TODO: more field values; need to be standard fields
		for field, value in dict(title=image.name).iteritems():
			FieldValue.objects.create(
				record=record,
				field=standardfield(field),
				order=n,
				value=value)
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
			imagesjs = simplejson.loads(request.POST.get('id', '[]'))
			images = map(self.searcher.getImage, imagesjs)
			urlmap = dict([(i.url, i) for i in images])
			urls = urlmap.keys()
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
