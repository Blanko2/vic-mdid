from django.shortcuts import render_to_response
from django.template import RequestContext
from rooibos.ui.views import select_record
from django.utils import simplejson
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue

def search(request):
	query = request.GET.get('q', '') or request.POST.get('q', '')
	return render_to_response('dummy-results.html',
		{
			'results': [
				{
					'thumb_url': 'http://losersbracket.com/wp-content/uploads/2011/09/blah.jpg',
					'title': 'blah',
					'record_url': 'http://losersbracket.com/wp-content/uploads/2011/09/blah.jpg'
				}
			]
		}, context_instance=RequestContext(request))

def _dummy_record(title, url):
	print '** _dummy_record (%s, %s)' % (title, url)
	record = Record.objects.create(name=title,
					source=url,
					manager='dummy')
	print '** _dummy_record.foo'
	FieldValue.objects.create(record=record,
				field=standardfield('title'),
				order=0,
				value=title)
	collection = _get_collection()
	print '** _dummy_record.bar'
	CollectionItem.objects.create(collection=collection, record=record)
	print '** _dummy_record.baz'
	job = JobInfo.objects.create(func='dummy_download_media', arg=simplejson.dump({
		'record': record.id,
		'url': url
	}))
	print '** _dummy_record.qux'
	job.run()
	return record

def _get_collection():
	print '** _get_collection'
	print '** %s' % Collection.objects.get_or_create
	collection, created = Collection.objects.get_or_create(name='dummy',
								defaults={
									'title': 'Dummy collection',
									'hidden': True,
									'description': 'Collection for dummy search thing'
								})
	print '** _get_collection.foo'
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=collection, usergroup=authenticated_users, read=True)
	print '** _get_collection.bar'
	return collection

def _get_storage():
	storage, created = Storage.objects.get_or_create(name='dummy',
								defaults={
									'title': 'Dummy collection',
									'hidden': True,
									'description': 'Collection for dummy search thing',
									'base': os.path.join(settings.AUTO_STORAGE_DIR, 'dummy')
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
		urls = simplejson.loads(request.POST.get('id', '[]'))
		ids = dict(Record.objects.filter(source__in=urls, manager='dummy').values_list('source', 'id'))
		result = []
		for url in urls:
			print '*** url %s' % url
			id = ids.get(url)
			if id:
				print '** baz'
				result.append(id)
			else:
				print '** qux'
				record = _dummy_record("blah", url)
				print '*** record = %s' % record
				result.append(record.id)
		r = request.POST.copy()
		r['id'] = simplejson.dumps(result)
		request.POST = r
	return select_record(request)
