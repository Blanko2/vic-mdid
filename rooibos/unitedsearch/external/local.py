import json
import urllib2
import re
from rooibos.unitedsearch import RecordImage, MapParameter, Result, ResultImage
from rooibos.unitedsearch.common import *
from rooibos.settings_local import *
from rooibos.unitedsearch.external.translator.query_language import Query_Language

name = "Local"
identifier = "local"
LOGO_URL = "http://collectiveaccess.org/graphics/CAlogo.gif"
BASE_URL = "http://barretts.ecs.vuw.ac.nz:8585/providence/app/lib/ca/Search/MdidSearcher.php?"
HOMEPAGE_URL = "barretts.ecs.vuw.ac.nz:8585/pawtucket"

def search(term, params, off, len):
    print "Local search: "
    print "Term = "+term
    print "Params = "+str(params)
    if not term and not params:
        return Result(0, 1), {}
    if not params:
        query_language = Query_Language(identifier)
        query_terms = query_language.searcher_translator(term)
        print "Query_terms = "+str(query_terms)
        params = query_terms
    url = build_url(params, off, len)
    raw_data = get_data(url)
    data, count, num_results = parse_data(raw_data)
    nextOff = int(off)+int(num_results)
    result = Result(count, nextOff if nextOff < count else count)
    for i in data.keys():
        image = data[i]
        result.addImage(ResultImage(image["url"], image['thumb'], image['name'], json.dumps(image)))
    return result, {}
"""
	off = int(off)
	from rooibos.solr.views import run_search
	sobj = run_search(AnonymousUser(),
		keywords=term,
		sort="title_sort desc",
		page=int(off/len if len > 0 else 0) + 1,
		pagesize=len)
	hits, records = sobj[0:2]
	result = Result(hits, off + len if off + len < hits else None)
	for i in records:
		result.addImage(ResultRecord(i, str(i.id)))
	return result
"""

def build_url(params, off, len):
    if 'keywords' in params:
        keywords = params['keywords']+" "
        del params['keywords']
    else:
        keywords = ""
    url = BASE_URL+"q="
    url += keywords#.replace(" ", "+")
    pref = ""
    for key in params:
        url += pref+build_param(key.strip(" "), params[key].strip(" "))
        pref = " "
    url += "&start="+str(off)
    url += "&end="+str(int(off)+int(len))
    return url.replace(" ", "%20")

def build_param(param, value):
    mod = ""
    if param.startswith("+") or param.startswith("-"):
        mod, param = param.split("_", 1)
    if " " in value:
        value = "("+value+")"
    ans = mod +("" if param in "keywords" else param+":")+value
    return ans
    
def parse_data(raw_data):
    #print "raw_data type:"+str(raw_data.__class__)
    if not raw_data:
        return {}, 0, 0
    count = re.findall("[0-9]+", raw_data)[0]
    count = int(count) if count else 0
    data = raw_data.strip("0123456789")
    #print "local.py, count = "+str(count)+", data("+str(data.__class__)+") = "+str(data)
    data = json.loads(data)
    for k in data.keys():
        data[k] = json.loads(data[k])
    num_results = len(data)
    return data, count, num_results

    
def get_data(url):
    print "lacal.py getting data from url: "+str(url)
    opener = proxy_opener()
    data = opener.open(url)
    html = ""
    for line in data:
        html += line
    return html
    
def previousOffset(off, len):
	off = int(off)
	return off > 0 and str(off - len)
	
def count(keyword):
    query_language = Query_Language(identifier)
	query_terms = query_language.searcher_translator(keyword)
	url = build_url(query_terms, 0, 1)
    raw_data = get_data(url)
    data, count, num_results = parse_data(raw_data)
    return count

def getImage(identifier):
    print "in local.py getImage, identifier = "+identifier
    data = json.loads(identifier)
    url = BASE_URL + "?get="+data['id']
    meta = get_data(url).strip("0123456789")
    meta = json.loads(meta)
    #img = RecordImage(data['url'], data['thumb'], data['name'], {'idno':data['idno'], 'name':data['name'], 'Artist':data['artist']}, json.dumps(data))
    img = RecordImage(data['url'], data['thumb'], data['name'], meta, json.dumps(data))
    print "made image"
    return img

def get_logo():
    return LOGO_URL

def get_searcher_page():
    return HOMEPAGE_URL
    
parameters = MapParameter({})
