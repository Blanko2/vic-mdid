import json
import urllib2
from rooibos.federatedsearch.searchers import *
#from searcher import *
from urllib import urlencode

from django.conf import settings

name = "DigitalNZ"

def _get(url):
	return urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
#	return urllib2.urlopen(url)

def __search(term, off, len):
	return json.load(_get("http://api.digitalnz.org/v3/records.json?" + urlencode({ 'api_key': settings.DIGITALNZ_KEY, 'text': term, 'per_page': len })))["search"]

def _count(searchobj):
	return searchobj["result_count"]

def count(term):
	return _count(_search(term))

# search(searchobj) :: [(name, thumburl, fullurl)]
#def _search(searchobj):
#	return filter(lambda(t): all(map(lambda(v): v != None, t)), map(lambda(v): (v["title"], v["thumbnail_url"], v["object_url"]), searchobj["results"]))

def search(term, params, off, len):
	obj = __search(term, off, len)
	result = Result(_count(obj), off + len)
	for i in obj["results"]:
		if(i["object_url"] != None):
			result.addImage(Image(i["object_url"], i["thumburl_url"], i["title"], i))
	return result
