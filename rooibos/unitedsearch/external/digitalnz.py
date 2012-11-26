import json
import urllib2
from rooibos.unitedsearch import *
from urllib import urlencode
from rooibos.unitedsearch.common import *
from django.conf import settings

name = "DigitalNZ"
identifier = "digitalnz"

BASE_IMAGE_LOCATION_URL="http://www.digitalnz.org/records?"
API_KEY="sfypBYD5Jpu1XqYBipX8"

"""
due to the way that DigitalNZ treats parameters it is easier to always treat a search as an 
advanced search
"""
def build_URL(query, params):
  # http://www.digitalnz.org/records?i[dnz_type]=Specimen&i[format]=Images&i[year]=[1620+TO+1940]&text=gug
  # parse query into parameters -- format will always be image
  # formats that need to be compensated for: start date, end date, (dnz_type)=> type? 
  
  break_query(query) 
  
  return 'h','k' 

def _get(url):
	return urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
#	return urllib2.urlopen(url)

def __search(query, off, len):
	# TODO: figure out how to only get results with .object_url/.large_thumbnail_url
	return json.load(_get("http://api.digitalnz.org/v3/records.json?" + urlencode({ 'api_key': settings.DIGITALNZ_KEY, 'text': query, 'page': int(off/len if len > 0 else 0) + 1, 'per_page': len, 'and[category][]': 'Images' })))["search"]

def _count(searchobj):
	return searchobj["result_count"]

def count(query):
	#TODO: do a proper implementation
	return 12345
	#return _count(_search(query))

def search(query, params, off, len):
	off = int(off)
	obj = __search(query, off, len)
	hits = _count(obj)
	result = Result(hits, off + len if off + len < hits else None)
  # build the URL 
  # url = build_URL(query, params)

	for i in obj["results"]:
		u = i["object_url"] or i["large_thumbnail_url"] or None
		# TODO: digitalnz's "Get Metadata API" doesn't seem to work---something better than using a JSON string as an identifier
		result.addImage(ResultImage(i["source_url"], i["thumbnail_url"], i["title"], u and json.dumps(i)))
	return result, {}


def getImage(identifier):
	i = json.loads(identifier)
	u = i["object_url"] or i["large_thumbnail_url"]
	return Image(u, i["thumbnail_url"], i["title"], i, identifier)

def previousOffset(off, len):
	off = int(off)
	return off > 0 and str(off - len)


# would result in something like { "category": "images", "year": [1984] } being passed.
parameters = MapParameter({
  "start date": OptionalParameter(ScalarParameter("start date"),"Start Date"),
  "end date": OptionalParameter(ScalarParameter("end date"), "End Date"),
  "type": OptionalParameter(ScalarParameter("type"), "Type"),
  "all": ScalarParameter(str,"All")
  })

