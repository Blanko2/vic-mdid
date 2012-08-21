from django.utils import simplejson
from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.util import guess_extension
from views import _get_storage
import logging
import mimetypes
import urllib2

print '** found dummy workers'

@register_worker('dummy_download_media')
def dummy_download_media(job):
	print '** dummy_download_media'
	logging.info('dummy download media started for %s' % job)
	jobinfo = None
	while jobinfo == None:
		try:
			jobinfo = JobInfo.objects.get(id=job.arg)
		except Exception, ex:
			print ex

	try:
		print "** foo"
		if jobinfo.status.startswith == 'Complete':
			return
		print "** bar"
		arg = simplejson.loads(jobinfo.arg)
		record = Record.objects.get(id=arg['record'], manager='dummy')
		url = arg['url']
		print "** baz"
		storage = _get_storage()
#		file = urllib2.urlopen(url)
		file = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
		setattr(file, 'size', int(file.info().get('content-length')))
		mimetype = file.info().get('content-type')
		print "** 4"
		media = Media.objects.create(record=record,
						storage=storage,
						name=record.name,
						mimetype=mimetype)
		media.save_file(record.name + guess_extension(mimetype), file)
		print "** 5"
		jobinfo.complete('Complete', 'File downloaded')
		print "** 6"
	
	except Exception, ex:
		logging.info('dummy download media failed for %s (%s)' % (job, ex))
		jobinfo.update_status('Failed: %s' % ex)
