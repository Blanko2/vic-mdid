import flickrapi
import urllib, urllib2, time
from os import makedirs
from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from forms import UploadFileForm
from rooibos.solr.models import SolrIndexUpdates 
from rooibos.solr import SolrIndex
from rooibos.converters.models import PowerPointUploader
from rooibos.ui.templatetags.ui import session_status_rendered	
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response


def main(request):
    return render_to_response('converters_main.html', {},
                              context_instance=RequestContext(request))
def powerpoint_main(request):
    if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		# Save the Power Point slides using the current time stamp to prevent toe stepping
		temp_full_path = settings.SCRATCH_DIR+str(time.time())+".ppt"
		if form.is_valid():
			# Save uploaded file to the scratch directory
			handle_uploaded_file(request.FILES['file'],temp_full_path)
			# Convert Power Point slides to images and import
			converter = PowerPointUploader()
			try:
				converter.convert_ppt(request.REQUEST['title'],request.REQUEST['slide_count'],temp_full_path)
			except Exception, detail:
			    return render_to_response('powerpoint_main.html', {'form': form,'error': detail},
										context_instance=RequestContext(request))
			return render_to_response('powerpoint_main.html', {'form': form,'success':1},
		                              context_instance=RequestContext(request))
    else:
    	# Display Upload Form
        form = UploadFileForm()
    return render_to_response('powerpoint_main.html', {'form': form},
                              context_instance=RequestContext(request))

def handle_uploaded_file(f,temp_full_path):
    destination = open(temp_full_path, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
