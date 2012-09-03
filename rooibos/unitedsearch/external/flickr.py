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

# search(searchobj) :: [(name, thumburl, fullurl)]
#def _search(searchobj):
#	return filter(lambda(t): all(map(lambda(v): v != None, t)), map(lambda(v): (v["title"], v["thumbnail_url"], v["object_url"]), searchobj["results"]))

def search(term, params, off, len):
	fs = fed.search(term, page=int(off/len if len > 0 else 0) + 1, pagesize=len)
	result = Result(fs["hits"], off + len)
	for i in fs["records"]:
		result.addImage(Image(i["record_url"], i["thumb_url"], i["title"], i, json.dumps(i)))
	return result

def getImage(identifier):
	i = json.loads(identifier)
	return Image(i["record_url"], i["thumb_url"], i["title"], i, identifier)
