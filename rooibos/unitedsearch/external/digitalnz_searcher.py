import json
import urllib2
from rooibos.unitedsearch.external.digitalnz import request, response 
from rooibos.unitedsearch import *
from urllib import urlencode
from rooibos.unitedsearch.common import *
from django.conf import settings


name = "DigitalNZ"
identifier = "digitalnz"

FORMAT_FINAL = "image"

BASE_IMAGE_LOCATION_URL="http://www.digitalnz.org/records?"
# TODO get a University API key instead of a personal one
API_KEY="sfypBYD5Jpu1XqYBipX8"

"""
Builds the URL:
    if there is anything inside params for the search it returns a complex URL - otherwise it returns a simple URL
"""
def build_URL(query, params):
    # URL format= http://www.digitalnz.org/records?i[dnz_type]=Specimen&i[format]=Images&i[year]=[1620+TO+1940]&text=gug
    # parse query into parameters -- format will always be image
    # formats that need to be compensated for: start date, end date, (dnz_type)=> type? 
    keywords, para_map = break_query_string(query) 
    url = ""
    if not para_map or len(para_map_)==0:
        url =  build_simple_URL(keywords)
    else:
        url =  build_complex_URL(keywords, para_map)
    return url 

def _get(url):
    return urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
# return urllib2.urlopen(url)

def __search(query, off, len):
    # TODO: figure out how to only get results with .object_url/.large_thumbnail_url
    #return json.load(_get("http://api.digitalnz.org/v3/records.json?" + urlencode({ 'api_key': self.API_KEY 'text': query, 'page': int(off/len if len > 0 else 0) + 1, 'per_page': len, 'and[category][]': 'Images' })))["search"]
    return ""

def _count(searchobj):
    return 1 

def count(query):
    #TODO: do a proper implementation
    return 12345
    #return _count(_search(query))

def search(query, params, off, len):
    """
    off = int(off)
    obj = __search(query, off, len)
    hits = _count(obj)
    result = Result(hits, off + len if off + len < hits else None)
    """
    # build the URL 
    url = build_URL(query, params)
    return Result(0,0), {}
    """
    for i in obj["results"]:
        u = i["object_url"] or i["large_thumbnail_url"] or None
        # TODO: digitalnz's "Get Metadata API" doesn't seem to work---something better than using a JSON string as an identifier
        result.addImage(ResultImage(i["source_url"], i["thumbnail_url"], i["title"], u and json.dumps(i)))
    return result, {}
    """

def getImage(identifier):
    i = json.loads(identifier)
    u = i["object_url"] or i["large_thumbnail_url"]
    return Image(u, i["thumbnail_url"], i["title"], i, identifier)

def previousOffset(off, len):
    off = int(off)
    return off > 0 and str(off - len)


parameters = MapParameter({
    "start date": OptionalParameter(ScalarParameter("start date"),"Start Date"),
    "end date": OptionalParameter(ScalarParameter("end date"), "End Date"),
    "type": OptionalParameter(ScalarParameter("type"), "Type"),
    "copyright": OptionalParameter(ScalarParameter("copyright"), "Copyright"),
    "all": ScalarParameter(str,"All")
    })


"""
=======================
URL BUILDERS###########
=======================
"""

"""
returns a simple search using the digitalNZ API
"""
def build_simple_URL(keywords):
    req = request.DigitalNZAPI(API_KEY)
    result = req.search(search_text="shed automobiles")
    print 'digitalNZ L~90'
    print result.data.keys()   
    return result

"""
returns a complex search using the digitalNZ API
"""
def build_complex_URL(keywords, para_map):
    params, unsupported_parameters = merge_dictionaries(para_map, params, parameters.parammap.keys())
    year = ''  
    if params["start_date"] and params['start_date'] != "":
        year+= format_date(params['start_date']) +' TO '
    else:
        year+= '1500 TO '    
    if params['end_date'] and params['end_date'] != "": 
        year+= format_date(params['end_date'])
    else:
        year+= '3000'
