"""DigitalNZ searcher - Uses the DigitalNZ API v3 for all calls

documentation for the digitalNZ API can be found at http://www.digitalnz.org/developers/api-docs-v3/search-records-api-v3
you can also find the getMetaData API at http://www.digitalnz.org/developers/api-docs-v3/get-metadata-api-v3
Calls to the digitalnz API can return a json, rss or xml - this system uses json and then loads it to a python object
DigitalNZ can handle modifiers and an empty keywords field, as long as there are other parameters to search by.
You will need to get your own API key and place it in settings_local.py as DNZ_API_KEY the URL builder here will 
    load it up
"""
import json
import urllib2
from urllib import urlencode
from rooibos.unitedsearch.common import break_query_string, merge_dictionaries, proxy_opener , list_to_str
from django.conf import settings
from rooibos import settings_local
import rooibos.unitedsearch as unitedsearch
from rooibos.unitedsearch import MapParameter, ScalarParameter, OptionalParameter, UserDefinedTypeParameter, DefinedListParameter,DoubleParameter, ListParameter
from rooibos.unitedsearch.external.translator.query_language import Query_Language 
from rooibos.unitedsearch.external.translator.digitalnz_dict import query_dict 

name = "DigitalNZ"
identifier = "digitalnz"

API_KEY = settings_local.DNZ_API_KEY
CATEGORY_VALUE="&and[category][]=Images"
#rights exist but I can't find out where the parameters for them lie
RIGHTS_VALUE="&and[rights][]="

LOGO_URL="http://www.digitalnz.org/system/resources/\
BAhbBlsHOgZmSSIsMjAxMi8wNy8yMC8xNF80NF8yNF80ODVfZG56X3Bvd2VyZWQuZ2lmBjoGRVQ/dnz_powered.gif"
SEARCHER_URL="http://digitalnz.org/"
BASE_IMAGE_LOCATION_URL="http://www.digitalnz.org/records?"
BASE_METADATA_LOCATION_URL="http://api.digitalnz.org/v3/records/"
END_METADATA_LOCATION_URL=".json?api_key="+API_KEY

BASE_SEARCH_API_URL="http://api.digitalnz.org/v3/records.json?api_key="+API_KEY

#This is meant to block the API from searching any partners that do not allow their images
# to be collected ie: no way to access the original image file
BLOCKED_CONTENT_PARTNERS="&without[content_partner][]=The%20University%20of%20Auckland%20Library"
# TODO get a University API key instead of a personal one

def search(query, params, offset, per_page=20):
    """performs the search and returns a results page and the used parameters"""
    # build the URL 
    if (not query or query in "keywords=, params={}") and (not params or params=={}):
        return unitedsearch.Result(0, offset), get_empty_params()
    offset = _modulate_offset(int(offset), per_page)
    next_offset = offset+per_page
    page = offset/per_page +1 
    url ,arg = _build_URL(query, params, per_page, page)
    result_object = _load_url(url) 
    hits = _count(url)
    print url
    result = unitedsearch.Result(hits, next_offset) 
    # add images
    for iobject in result_object["search"]["results"]:
        thumbnail_url = iobject["thumbnail_url"] or iobject["large_thumbnail_url"] or iobject["object_url"] or None 
        # should only be done after fixing getImage()
        provider = iobject["content_partner"][0] or iobject["display_content_partner"][0]
        image = unitedsearch.ResultImage(iobject["source_url"], thumbnail_url, iobject["title"], iobject["id"], content_provider=provider)
        result.addImage(image)
    return result, arg 

def previousOffset(offset, per_page):
    """ the image offset for the previous page """
    offset = int(offset)
    return offset > 0 and str(offset - per_page)

def count(query, parameters={}):
    if not query or query in "keywords=, params={}":
        return 0
    """ returns the number of hits"""
    search_object = _load(query, parameters) 
    hits = int(search_object["search"]["result_count"]) 
    return hits 

def _count(url):
    result_json = _get_url(url)    
    search_object = json.load(result_json)
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
        params -- params from the sidebar - if these exist then there shou    print "keywords =========== "
    print keywordsldn't be a query
        per_page -- number of images per page
        page -- page to retrieve images from
    """
    # keywords, para_map = break_query_string(query) 
    url = ""
    query_terms = params.copy() if params else _translate_query(query) #if not params else parse_parameters(params)
    return  _build_simple_URL(query_terms, per_page, page)


def _build_simple_URL(query_terms, per_page, page):
    """ returns a search url with all the given keywords, at the given page and with the number or specified results per page """
    print query_terms
    facets=""
    keywords=""
    arg = get_empty_params()
    facet_arg = []
    query_string = ""
    sidebar = True
    if 'query_string' in query_terms:
        query_string=query_terms['query_string']   
        arg.update({"query_string":query_string})
        sidebar = False
        del query_terms['query_string']
    if 'keywords' in query_terms:
        keywords= list_to_str(query_terms['keywords'])
        arg.update({"keywords":keywords})
        if sidebar:
            query_string = list_to_str(query_terms['keywords'])
        del query_terms['keywords']
    
    for q in query_terms:
        q_split = q.split('_')
        if len(q_split)>1:   
            query_mod = q_split[0]
            facet = q[len(query_mod)+1:]
        else:   
            query_mod = 'and'
            facet = q
        
        if facet == "keywords":
            keywords += " "+list_to_str(query_terms[q])
        else:
            value_list = query_terms[q]
            if not isinstance(value_list,list):
                value_list = [value_list]
            for value in value_list:
                facets += '&'+query_mod+'['+facet+'][]='+value
        
        value_list = query_terms[q]
        if not isinstance(value_list,list):
            value_list = [value_list]
        for value in value_list:
            if sidebar and not facet=="keywords":
                query_string += ","+query_dict[query_mod]+query_dict[facet]+"="+value

            if facet!= "keywords":
                facet_arg.append([query_mod,[facet,value]])

    keywords = keywords.replace(" ","+")
    if not "query_string" in arg:
        while "''" in query_string:
            query_string = query_string.replace(",,",",")
        if query_string.startswith(","):
            query_string = query_string[1:]
        while query_string.endswith(","):
            query_string.pop()
        arg['query_string'] = query_string
    url = BASE_SEARCH_API_URL+"&text="+keywords+BLOCKED_CONTENT_PARTNERS+facets+CATEGORY_VALUE+"&per_page="+str(per_page)+"&page="+str(page)
    while len(facet_arg)<5:
        facet_arg.append([])
    arg.update({"field":facet_arg})
    
    print url
    return url, arg 
"""
================
#TOOLS
================
"""
def _translate_query(query):
    """ translates from universal query language to dnz query language """
    translator = Query_Language(identifier) 
    query_terms = translator.searcher_translator(query)
    return query_terms

def _get_url(url):
    """ retrieves the created url """
    proxy_url = proxy_opener()
    html = proxy_url.open(url)
    return html 

def _load_url(url):
    """ Returns a python object from the resulting json string from the given url """
    return json.load(_get_url(url))

def _load(query, params):
    """ creates a url from a given query and loads the resulting json string into a python object """
    # should build a url and return the json string that it returns
    url,arg  = _build_URL(query, params, 20, 1)
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

def get_searcher_page():
    return SEARCHER_URL

def get_logo():
    return LOGO_URL

def getImage(identifier):
    #TODO parse html when cannot find a location_url 
    identifier = str(identifier)
    url = BASE_METADATA_LOCATION_URL+identifier+END_METADATA_LOCATION_URL
    image_object = _load_url(url)['record'] 
    #print image_object
    location_url = image_object["object_url"] or image_object["large_thumbnail_url"]
    thumbnail_url = image_object["thumbnail_url"]
    title = image_object["title"]
    if not location_url or location_url == "":
        source_url = image_object["source_url"]
        empty = "/static/images/thumbnail_unavailable.png"
        img = unitedsearch.RecordImage(source_url, empty, title, image_object, identifier) 
    else:
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

field_types = ['creator',
    'display_collection',
    'placename',
    'year',
    'decade',
    'century',
    'language',
    'content_partner',
    'rights',
    'collection']

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


