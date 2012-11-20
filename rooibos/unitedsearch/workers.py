from django.utils import simplejson
from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.util import guess_extension
from common import get_storage
import logging
import mimetypes
import urllib2

@register_worker('unitedsearch_download_media')
def dummy_download_media(job):
	logging.info('unitedsearch download media started for %s' % job)
	jobinfo = None
	while jobinfo == None:
		try:
			jobinfo = JobInfo.objects.get(id=job.arg)
		except Exception, ex:
			print ex

	try:
		if jobinfo.status.startswith == 'Complete':
			return
		arg = simplejson.loads(jobinfo.arg)
		record = Record.objects.get(id=arg['record'], manager='unitedsearch')
		url = arg['url']
		storage = get_storage()
#		file = urllib2.urlopen(url)
		file = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128", "https": "http://localhost:3128"})).open(url)
		setattr(file, 'size', int(file.info().get('content-length')))
		mimetype = file.info().get('content-type')
		media = Media.objects.create(record=record,
						storage=storage,
						name=record.name,
						mimetype=mimetype)
		ext = guess_extension(mimetype)
		extension = guess_extension(mimetype)
		if not extension :		# wasn't a matched pattern
			extension = ""
		#media.save_file(record.name + guess_extension(mimetype), file)
		media.save_file(record.name + extension, file)
		jobinfo.complete('Complete', 'File downloaded')
	
	except Exception, ex:
		logging.info('unitedsearch download media failed for %s (%s)' % (job, ex))
		jobinfo.update_status('Failed: %s' % ex)
