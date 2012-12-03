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
BASE_SEARCH_API_URL="http://api.digitalnz.org/v3/records.rss?api_key="+API_KEY

# TODO get a University API key instead of a personal one
def search(query, params, offset, per_page):
    # build the URL 
    offset = modulate_offset(int(offset), per_page)
    page = offset/per_page +1 
    url = _build_URL(query, params, per_page, page)
    return params 

def previousOffset(offset, per_page):
    offset = int(offset)
    return offset > 0 and str(offset - per_page)

def count(query):
   return 1234 

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
    # need to put all params into keywords because
    # dnz API accepts no useful parameters 
    for p in params:
        keywords+= "+"+p
    for p in para_map:
        keywords+= "+"+p
    url =  _build_simple_URL(keywords, per_page, page)
    return url 


"""
returns a search using the digitalNZ API
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

def get_image(identifier):
    i = json.loads(identifier)
    u = i["object_url"] or i["large_thumbnail_url"]
    return Image(u, i["thumbnail_url"], i["title"], i, identifier)

def modulate_offset(offset, per_page):
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

