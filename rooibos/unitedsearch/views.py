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
			{ 'results': [ { 'thumb_url': i.thumb, 'title': i.name, 'record_url': i.url } for i in results ] },
			context_instance=RequestContext(request))

	def record(self, identifier):
		image = self.searcher.getImage(identifier)
		record = Record.objects.create(name=image.name,
						source=image.url,
						manager='unitedsearch')
		n = 0
		for field, value in dict(image.meta, title=image.name).iteritems():
			FieldValue.objects.create(
				record=record,
				field=standardfield(field),
				order=n,
				value=value)
			n += 1
		collection = self.get_collection()
		CollectionItem.objects.create(collection=collection, record=record)
		job = JobInfo.objects.create(func='unitedsearch_download_media', arg=simplejson.dumps({
			'record': record.id,
			'url': image.url
		}))
		job.run()
		return record

	def get_collection(self):
		collection, created = Collection.objects.get_or_create(
			name='unitedsearch',
			defaults={
				'title': 'United Search collection',
				'hidden': True,
				'description': 'Collection for images retrieved through the United Search'
			})
		if created:
			authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
			AccessControl.objects.create(content_object=collection, usergroup=authenticated_users, read=True)
		return collection

	def get_storage(self):
		storage, created = Storage.objects.get_or_create(
			name='unitedsearch',
			defaults={
				'title': 'United Search collection',
				'system': 'local',
				'base': os.path.join(settings.AUTO_STORAGE_DIR, 'unitedsearch')
			})
		if created:
			authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
			AccessControl.objects.create(content_object=storage, usergroup=authenticated_users, read=True)
		return storage

	def select(request):
		print '** select %s' % request
		if not request.user.is_authenticated():
			raise Http404()
		
		print '** foo'
		if request.method == "POST":
			print '** bar'
			print '*** urls %s' % request.POST.get('id', '[]')
			identifier = simplejson.loads(request.POST.get('id', '[]'))
			ids = dict(Record.objects.filter(source__in=urls, manager='unitedsearch').values_list('source', 'id'))
			result = []
			for url in urls:
				print '*** url %s' % url
				id = ids.get(url)
				if id:
					print '** baz'
					result.append(id)
				else:
					print '** qux'
					record = self.record(url)
					print '*** record = %s' % record
					result.append(record.id)
			r = request.POST.copy()
			r['id'] = simplejson.dumps(result)
			request.POST = r
		return select_record(request)
