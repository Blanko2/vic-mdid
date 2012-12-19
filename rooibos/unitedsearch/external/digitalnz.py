import json
import urllib2
from urllib import urlencode
from rooibos.unitedsearch.common import break_query_string, merge_dictionaries, proxy_opener 
from django.conf import settings
from rooibos import settings_local
import rooibos.unitedsearch as unitedsearch
from rooibos.unitedsearch import MapParameter, ScalarParameter, OptionalParameter, UserDefinedTypeParameter, DefinedListParameter,DoubleParameter, ListParameter
from rooibos.unitedsearch.external.translator.query_language import Query_Language 
from digitalnz_parser import parse_parameters

name = "DigitalNZ"
identifier = "digitalnz"

API_KEY = settings_local.DNZ_API_KEY
CATEGORY_VALUE="&and[category][]=Images"
#rights exist but I can't find out where the parameters for them lie
RIGHTS_VALUE="&and[rights][]="

LOGO_URL="http://www.digitalnz.org/system/resources/BAhbBlsHOgZmSSIsMjAxMi8wNy8yMC8xNF80NF8yNF80ODVfZG56X3Bvd2VyZWQuZ2lmBjoGRVQ/dnz_powered.gif"
BASE_IMAGE_LOCATION_URL="http://www.digitalnz.org/records?"
BASE_METADATA_LOCATION_URL="http://api.digitalnz.org/v3/records/"
END_METADATA_LOCATION_URL=".json?api_key="+API_KEY

BASE_SEARCH_API_URL="http://api.digitalnz.org/v3/records.json?api_key="+API_KEY

# TODO get a University API key instead of a personal one

def search(query, params, offset, per_page=20):
    # build the URL 
    if not query and params=={}:
        return unitedsearch.Result(0, offset), get_empty_params()
    offset = _modulate_offset(int(offset), per_page)
    next_offset = offset+per_page
    page = offset/per_page +1 
    url = _build_URL(query, params, per_page, page)
    result_object = _load_url(url) 
    hits = count(query, parameters = params) 
    result = unitedsearch.Result(hits, next_offset) 
    # add images
    for object in result_object['search']["results"]:
        thumbnail_url = object["object_url"] or object["large_thumbnail_url"] or None 
        image = unitedsearch.ResultImage(object["source_url"], thumbnail_url, object["title"], object["id"])
        result.addImage(image)
    return result, get_empty_params() 

def previousOffset(offset, per_page):
    """ the image offset for the previous page """
    offset = int(offset)
    return offset > 0 and str(offset - per_page)

def count(query, parameters={}):
    """ returns the number of hits"""
    search_object = _load(query, parameters) 
    hits = int(search_object["search"]["result_count"]) 
    return hits 

"""
=======================
URL BUILDERS###########
=======================
"""
def _build_URL(query, params, per_page, page):
    """
    Builds the URL:
        query -- the query received by the searcher
        params -- params from the sidebar - if these exist then there shouldn't be a query
        per_page -- number of images per page
        page -- page to retrieve images from
    """
    # keywords, para_map = break_query_string(query) 
    url = ""
    query_terms = _translate_query(query) if not params else parse_parameters(params)
    url =  _build_simple_URL(query_terms, per_page, page)
    return url 

def _build_simple_URL(query_terms, per_page, page):
    """ returns a search url with all the given keywords, at the given page and with the number or specified results per page """
    facets=""
    keywords=""
    if 'text' in query_terms:
        keywords=query_terms['text']   
        del query_terms['text']
    for q in query_terms:
        q_split = q.split('_')
        if len(q_split)>1:   
            query_mod = q_split[0]
            facet = q_split[1] 
        else:   
            query_mod = 'and'
            facet = q
        facets += '&'+query_mod+'['+facet+'][]='+query_terms[q]
    keywords = keywords.replace(" ","+")
    url = BASE_SEARCH_API_URL+"&text="+keywords+facets+CATEGORY_VALUE+"&per_page="+str(per_page)+"&page="+str(page)
    return url 
"""
================
#TOOLS
================
"""
def _translate_query(query):
    """ checks if the query comes from the sidebar - if not, it needs translating"""
    translator = Query_Language(identifier) 
    query_terms = translator.searcher_translator(query)
    return query_terms

def _get_url(url):
    """ retrieves the created url """
    proxy_url = proxy_opener()
    print 'dnz ===108'
    print url
    html = proxy_url.open(url)
    return html 

def _load_url(url):
    """ Returns a python object from the resulting json string from the given url """
    return json.load(_get_url(url))

def _load(query, params):
    """ creates a url from a given query and loads the resulting json string into a python object """
    # should build a url and return the json string that it returns
    url = _build_URL(query, params, 20, 1)
    result_json = _get_url(url)    
    return json.load(result_json)


def _modulate_offset(offset, per_page):
    """ modulates the offset to match a multiple of the page length -- if offset%per_page!=0 it changes to be the closest value
    to it which makes offset%per_page==0 """ 
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

# ====== GETTERS ========
# =======================

def get_logo():
    return LOGO_URL

def getImage(identifier):
    url = BASE_METADATA_LOCATION_URL+identifier+END_METADATA_LOCATION_URL
    image_object = _load_url(url)['record'] 
    location_url = image_object["object_url"] or image_object["large_thumbnail_url"]
    thumbnail_url = image_object["thumbnail_url"]
    title = image_object["title"]
    img = unitedsearch.RecordImage(location_url, thumbnail_url, title, image_object, identifier) 
    return img 

def get_empty_params():
    return {
    "keywords":[],
    "creator":[],
    "century":[],
    "decade":[],
    "year":[],
    "field":[]
    }

"""
=============
PARAMETERS
=============
"""

field_types = ['category', 'display_collection', 'creator', 'placename', 'year', 'decade', 'century', 'language', 'content_partner', 'rights', 'collection']
modifier_types = ['and','or','without']

parameters = MapParameter({
    "keywords":ScalarParameter(str,label="keywords"),
    "field" : ListParameter([
        DoubleParameter(DefinedListParameter(modifier_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(modifier_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(modifier_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(modifier_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        )
        ],label="Facets")
    })


