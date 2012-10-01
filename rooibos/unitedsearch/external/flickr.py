import json
import urllib2
from rooibos.unitedsearch import *
#from searcher import *
from urllib import urlencode

from django.conf import settings
from rooibos.federatedsearch.flickr import FlickrSearch

name = "Flickr"
identifier = "flickr"

fed = FlickrSearch()
fed._licenses = {}

def search(term, params, off, len):
	if not term.strip():
		return Result(0, None)
	off = int(off)
	fs = fed.search(term, page=int(off/len if len > 0 else 0) + 1, pagesize=len)
	result = Result(fs["hits"], off + len if off + len < fs["hits"] else None)
	for i in fs["records"]:
		result.addImage(ResultImage(i["record_url"], i["thumb_url"], i["title"], json.dumps(i)))
	return result

def getImage(identifier):
	i = json.loads(identifier)
	info = fed.flickr.flickr_call(method='flickr.photos.getSizes',
					photo_id=i["flickr_id"],
					format='xmlnode')
	image_url = info.sizes[0].size[-1]['source']
	return Image(image_url, i["thumb_url"], i["title"], i, identifier)

parameters = MapParameter({})
