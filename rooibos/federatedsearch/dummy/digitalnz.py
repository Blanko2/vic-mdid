from django.conf import settings
import json
import urllib2
from urllib import urlencode

def _get(url):
	return urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
#	return urllib2.urlopen(url)

def _search(term):
	return json.load(_get("http://api.digitalnz.org/v3/records.json?" + urlencode({ 'api_key': settings.DIGITALNZ_KEY, 'text': term, 'per_page': 100 })))["search"]

def _count(searchobj):
	return searchobj["result_count"]

def count(term):
	return _count(_search(term))

# search(term) :: [(name, thumburl, fullurl)]
def search(term):
	return filter(lambda(t): all(map(lambda(v): v != None, t)), map(lambda(v): (v["title"], v["thumbnail_url"], v["object_url"]), _search(term)["results"]))
