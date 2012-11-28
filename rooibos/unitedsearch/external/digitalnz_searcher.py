import json
import urllib2
from urllib import urlencode
from rooibos.unitedsearch.common import break_query_string, merge_dictionaries 
from django.conf import settings


name = "DigitalNZ"
identifier = "digitalnz"

API_KEY="sfypBYD5Jpu1XqYBipX8"
BASE_IMAGE_LOCATION_URL="http://www.digitalnz.org/records?"
BASE_METADATA_LOCATION_URL="http://api.digitalnz.org/v3/records/"
BASE_SEARCH_API_URL="http://api.digitalnz.org/v3/records.rss?api_key="+API_KEY
# TODO get a University API key instead of a personal one
"""
NEED TO COMPLETELY REWRITE THIS CLASS SRSLY, NOT EVEN FUNNY
    WHAT NEEDS TO BE DONE:
        allow:
        -- per_page
        -- page
        -- and[Category][]=Images 

"""
def _get(url):
    return urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
# return urllib2.urlopen(url)

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
    url = _build_URL(query, params)
    return Result(0,0), params 
    """
    for i in obj["results"]:
        u = i["object_url"] or i["large_thumbnail_url"] or None
        # TODO: digitalnz's "Get Metadata API" doesn't seem to work---something better than using a JSON string as an identifier
        result.addImage(ResultImage(i["source_url"], i["thumbnail_url"], i["title"], u and json.dumps(i)))
    return result, {}
    """
def previousOffset(off, len):
    off = int(off)
    return off > 0 and str(off - len)


"""
=======================
URL BUILDERS###########
=======================
"""
"""
Builds the URL:
    if there is anything inside params for the search it returns a complex URL - otherwise it returns a simple URL
"""
def _build_URL(query, params):
    keywords, para_map = break_query_string(query) 
    url = ""
    # need to put all params into keywords because
    # dnz API accepts no useful parameters 
    for p in params:
        keywords+= " "+params[p]
    url =  _build_simple_URL(keywords)
    return url 


"""
returns a simple search using the digitalNZ API
"""
def _build_simple_URL(keywords):
    #TODO needs to do stuff.
    url = BASE_SEARCH_API_URL+
    return 'a'
"""
================
#TOOLS
================
"""

def get_image(identifier):
    i = json.loads(identifier)
    u = i["object_url"] or i["large_thumbnail_url"]
    return Image(u, i["thumbnail_url"], i["title"], i, identifier)

def check_valid_type(type):
    if type in dnz_valid_types:    
        return True
    else:
        return False

def check_valid_usage(usage):
    if usage in dnz_valid_usage:
        return True
    else:
        return False

