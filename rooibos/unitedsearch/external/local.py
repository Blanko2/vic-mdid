import json
import urllib2
from rooibos.unitedsearch import *
from urllib import urlencode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser

name = "Local"
identifier = "local"

def search(term, params, off, len):
	from rooibos.solr.views import run_search
	sobj = run_search(AnonymousUser(),
		keywords=term,
		sort="title_sort desc",
		page=int(off/len if len > 0 else 0) + 1,
		pagesize=len)
	hits, records = sobj[0:2]
	result = Result(hits, off + len)
	for i in records:
		# TODO: Reduce level of insanity.
		result.addImage(ResultImage(
			"javascript:preview_dialog({" +
				"attr: function(){" +
					"return \"" + i.get_absolute_url() + "\";" +
				"}" +
			"}," +
			"{" +
				"attr: function(n){" +
					"return n == \"src\"? \"" + i.get_thumbnail_url() + "\" :" +
						"n == \"id\"? \"record-id-" + str(i.id) + "\" :" +
						"n == \"alt\"? \"" + i.title + "\" : \"\";" +
				"}" +
			"})", i.get_thumbnail_url(), i.title, None))
	return result

# TODO: figure out a way to let the local search bypass US by giving back a record
def doNotGetImage(identifier):
	i = json.loads(identifier)
	info = fed.flickr.flickr_call(method='flickr.photos.getSizes',
					photo_id=i["flickr_id"],
					format='xmlnode')
	image_url = info.sizes[0].size[-1]['source']
	return Image(image_url, i["thumb_url"], i["title"], i, identifier)
