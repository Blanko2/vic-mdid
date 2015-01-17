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
	print "cheesecake"
	jobinfo = None
	while jobinfo == None:
		try:
			jobinfo = JobInfo.objects.get(id=job.arg)
		except Exception, ex:
			print 'oh no, i except'
	arg = simplejson.loads(jobinfo.arg)
	record = Record.objects.get(id=arg['record'], manager='unitedsearch')
	try:
		if jobinfo.status.startswith == 'Complete':
			return
		url = arg['url']
		print 'ready to download image at: ' + url
 		storage = get_storage()
		if storage:
			print 'storage in workers.py is valid at 32'
		else:
			print 'storage is invalid at 32'
		proxy = proxy_opener()
		# where you get a url error
		file = proxy.open(url)
		image_data = file.read()
		print 'unitedsearch.workers.py -- image_data: '+str(len(image_data))
		size = len(image_data)

		image_file=StringIO.StringIO(image_data)
		if image_file:
			print 'have image file'
		else:
			print 'do not have image file'
		#size = file.info().get('content-length')
		#setattr(file, 'size', int(size if size else 0))
		setattr(image_file, 'size', int(size if size else 0))
		mimetype = file.info().get('content-type')
		print 'mimetype is :' + mimetype
		file.close()
		if storage:
			print 'storage is valid in workers.py before 53'
		media = Media.objects.create(record=record,
						storage=storage,
						name=record.name,
						mimetype=mimetype)
		print "storage set!!!!!!11!!!1!!!!!!!11!!!1!!!!!1!!"
		ext = guess_extension(mimetype)
		extension = guess_extension(mimetype)
		if not extension :		# wasn't a matched pattern
			extension = ""
		#media.save_file(record.name + guess_extension(mimetype), file)
		print "saving file " + record.name + extension
		print record.name
		print extension
		media.save_file(record.name + extension, image_file)
		#media.save_file(record.name + extension, file)
		jobinfo.complete('Complete', 'File downloaded')
	
	except Exception, ex:
		logging.info('unitedsearch download media failed for %s (%s)' % (job, ex))
		jobinfo.update_status('Failed: %s' % ex)				
