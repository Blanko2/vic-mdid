from rooibos.workers import register_worker
from views import _get_storage

print '** found dummy workers'

@register_worker('dummy_download_media')
def dummy_download_media(job):
	print '** dummy_download_media'
	logging.info('dummy download media started for %s' % job)
	jobinfo = JobInfo.objects.get(id=job.arg)

	try:
		if jobinfo.status.startwith == 'Complete':
			return
		record = Record.objects.get(id=arg['record'], manager='dummy')
		url = arg['url']
		storage = _get_storage()
		file = urllib2.urlopen(url)
		setattr(file, 'size', int(file.info().get('content-length')))
		mimetype = file.info().get('content-type')
		media = Media.objects.create(record=record,
						storage=storage,
						name=record.name,
						mimetype=mimetype)
		media.save_file(record.name + guess_extension(mimetype), file)
		jobinfo.complete('Complete', 'File downloaded')
	
	except Exception, ex:
		logging.info('dummy download media failed for %s (%s)' % (job, ex))
		jobinfo.update_status('Failed: %s' % ex)
