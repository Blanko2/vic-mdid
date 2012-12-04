import json
import urllib2
from urllib import urlencode
from rooibos.unitedsearch.common import break_query_string, merge_dictionaries 
from django.conf import settings


name = "DigitalNZ"
identifier = "digitalnz"

API_KEY="sfypBYD5Jpu1XqYBipX8"
CATEGORY_VALUE="&and[category][]=Images"

BASE_IMAGE_LOCATION_URL="http://www.digitalnz.org/records?"
BASE_METADATA_LOCATION_URL="http://api.digitalnz.org/v3/records/"
END_METADATA_LOCATION_URL=".json?"+API_KEY

BASE_SEARCH_API_URL="http://api.digitalnz.org/v3/records.rss?api_key="+API_KEY

# TODO get a University API key instead of a personal one

def search(query, params, offset, per_page=20):
    # build the URL 
    offset = _modulate_offset(int(offset), per_page)
    nex_offset = offset+per_page
    page = offset/per_page +1 
    
    url = _build_URL(query, params, per_page, page)
    result_object = _load(url) 
    hits = count(query, parameters = params) 
    result = Result(hits, next_offset if next_offset < hits else None) 
    # add images
    for object in result_objecti["results"]:
        thumbnail_url = object["object_url"] or object["large_thumbnail_url"] or None 
        image = ResultImage(object["source_url"], thumbnail_url, object["title"], object["id"])
        result.addImage(image)
    
    return result,  params 

# not worked on but should work anyway
def previousOffset(offset, per_page):
    offset = int(offset)
    return offset > 0 and str(offset - per_page)

# count should be done
def count(query, parameters={}):
    # need to get result, get json that composes it and then
    # break that and get 'result_count' value
    keywords, params = break_query_string(query)
    if parameters != {}:
        params = merge_dictionaries(parameters, params, params.keys())
    search_object = _load(keywords, params) 
    hits = int(search_object["search"]["result_count"]) 
    
    return hits 

"""
=======================
URL BUILDERS###########
=======================
"""
"""
Builds the URL:
    there are only ever simple searches because digitalNZ has a weird search API that doesn't properly include its own filters
"""
def _build_URL(query, params, per_page, page):
    keywords, para_map = break_query_string(query) 
    url = ""
    # need to put all params and para_map into keywords because
    # dnz API accepts no useful parameters 
    for p in params:
        keywords+= "+"+p
    for p in para_map:
        keywords+= "+"+p
    url =  _build_simple_URL(keywords, per_page, page)
    return url 

"""
returns a search url with all the given keywords, at the given page and with the number or specified results per page
"""
def _build_simple_URL(keywords, per_page, page):
    keywords = keywords.replace(" ","+")
    url = BASE_SEARCH_API_URL+"&text="+keywords+CATEGORY_VALUE+"&per_page="+str(per_page)+"&page="+str(page)
    return url 
"""
================
#TOOLS
================
"""
def _get_url(url):
    return urllib2.urlopen(url)

"""
returns a python object from the resulting json string from the given url
"""
def _load(url):
    return json.load(_get_url(url))

"""
creates a url from a given query and loads the resulting json string into a python object
"""
def _load(keywords, params):
    # should build a url and return the json string that it returns
    return json.load(_get_url(_build_URL(keywords, params, 20, 1)))


# ====== GETTERS ========
# =======================

def getImage(identifier):
    url = BASE_METADATA_LOCATION_URL+identifier+END_METADATA_LOCATION_URL
    image_object = _load(url)['record'] 
    location_url = image_object["object_url"] or image_object["large_thumbnail_url"]
    thumbnail_url = image_object["thumbnail_url"]
    title = image_object["title"]
    return Image(location_url, thumbnail_url, title, image_object, identifier) 

"""
modulates the offset to match a multiple of the page length -- if offset%per_page!=0 it changes to be the closest value
to it which makes offset%per_page==0
""" 
def _modulate_offset(offset, per_page):
    modulate = offset%per_page 
    diff_mod = per_page - modulate
   
    if offset != 0 and modulate != 0:
        #offset = Minimum Necessary Change between the offset and a modulo of zero
        if modulate < diff_mod:
            offset -= modulate
        else:
            offset += diff_mod 
    # calculate the page
    page = offset/per_page + 1
    return offset

"""
++++++++++++++++++++++++++
OBSOLETE
"""
def _check_valid_type(type):
    if type in dnz_valid_types:    
        return True
    else:
        return False

def _check_valid_usage(usage):
    if usage in dnz_valid_usage:
        return True
    else:
        return False

