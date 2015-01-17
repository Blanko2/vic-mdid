from django.utils import simplejson
from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.workers import register_worker
from rooibos.workers.models import JobInfo
from rooibos.util import guess_extension
from common import get_storage
from rooibos.unitedsearch.common import proxy_opener
import logging
import mimetypes
import urllib2
import StringIO

@register_worker('unitedsearch_download_media')
def unitedsearch_download_media(job):
	logging.info('unitedsearch download media started for %s' % job)
	print "unitedsearch_download_media job starting"
	jobinfo = None
	while jobinfo == None:
		try:
			#print "get JobInfo: "+str(job.arg)
			jobinfo = JobInfo.objects.get(id=job.arg)
			#print "got JobInfo"
		except Exception, ex:
			print ex

	arg = simplejson.loads(jobinfo.arg)
	record = Record.objects.get(id=arg['record'], manager='unitedsearch')
	try:
		if jobinfo.status.startswith == 'Complete':
			print "JobInfo = Complete"
			return
		url = arg['url']
		storage = get_storage()
		proxy = proxy_opener()
		# where you get a url error
		file = proxy.open(url)
		image_data = file.read()
		size = len(image_data)

		image_file=StringIO.StringIO(image_data)
		#size = file.info().get('content-length')
		#setattr(file, 'size', int(size if size else 0))
		setattr(image_file, 'size', int(size if size else 0))
		mimetype = file.info().get('content-type')
		file.close()
		media = Media.objects.create(record=record,
						storage=storage,
						name=record.name,
						mimetype=mimetype)
		ext = guess_extension(mimetype)
		extension = guess_extension(mimetype)
		if not extension :		# wasn't a matched pattern
			extension = ""
		#media.save_file(record.name + guess_extension(mimetype), file)
		media.save_file(record.name + extension, image_file)
		#media.save_file(record.name + extension, file)
		print "unitedsearch_download_media job complete"
		jobinfo.complete('Complete', 'File downloaded')
	
	except Exception, ex:
		logging.info('unitedsearch download media failed for %s (%s)' % (job, ex))
		jobinfo.update_status('Failed: %s' % ex)				