import json
import urllib2
from rooibos.unitedsearch import *
from urllib import urlencode

from django.conf import settings

name = "DigitalNZ"
identifier = "digitalnz"

def _get(url):
	return urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
#	return urllib2.urlopen(url)

def __search(term, off, len):
	# TODO: figure out how to only get results with .object_url/.large_thumbnail_url
	return json.load(_get("http://api.digitalnz.org/v3/records.json?" + urlencode({ 'api_key': settings.DIGITALNZ_KEY, 'text': term, 'page': int(off/len if len > 0 else 0) + 1, 'per_page': len, 'and[category][]': 'Images' })))["search"]

def _count(searchobj):
	return searchobj["result_count"]

def count(term):
	return _count(_search(term))

def search(term, params, off, len):
	off = int(off)
	obj = __search(term, off, len)
	hits = _count(obj)
	result = Result(hits, off + len if off + len < hits else None)
	for i in obj["results"]:
		u = i["object_url"] or i["large_thumbnail_url"] or None
		# TODO: digitalnz's "Get Metadata API" doesn't seem to work---something better than using a JSON string as an identifier
		result.addImage(ResultImage(i["source_url"], i["thumbnail_url"], i["title"], u and json.dumps(i)))
	return result

def getImage(identifier):
	i = json.loads(identifier)
	u = i["object_url"] or i["large_thumbnail_url"]
	return Image(u, i["thumbnail_url"], i["title"], i, identifier)

# would result in something like { "category": "images", "year": [1984] } being passed.
parameters = MapParameter({ "category": ScalarParameter(str, "Category"), "year": OptionalParameter(ScalarParameter("year"), "Year") })
