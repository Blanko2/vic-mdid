"""Collective Access searcher - built around the collective access API for v1.3 and above

This searcher uses the python-requests library as opposed to urllib2
    http://docs.python-requests.org/en/latest/index.html
Documentation for the CA API can be found at 
    http://docs.collectiveaccess.org/
    http://docs.collectiveaccess.org/wiki/Web_Service_API
"""
import json
import urllib2
import requests
import re
import rooibos.unitedsearch as unitedsearch
from rooibos.settings_local import DEBUG, PROXY
from unitedsearch import RecordImage, Result, ResultImage
from unitedsearch import MapParameter, ScalarParameter, OptionalParameter, UserDefinedTypeParameter
from unitedsearch import DefinedListParameter, DoubleParameter, ListParameter
from unitedsearch.common import list_to_str, modulate_offset
from unitedsearch.external.translator.query_language import Query_Language 


name = "Collective Access"
identifier = "ca"
LOGO_URL = ""
BASE_URL = "http://54.66.138.173/ca14/service.php/find/"
HOMEPAGE_URL = "http://54.66.138.173/ca14/"

ORIGINAL_MEDIA = "ca_object_representations.media.original"
PREVIEW_MEDIA = "ca_object_representations.media.preview"
TITLE = "display_label"
ID = "object_id"

ADVANCED_DEBUG = False 

"""
The actual search method for the given searcher

term - search terms from default search
params - dict: search terms from advanced search tab
off - int: offset of search items for viewing next pages
len - int: length of page, ie: number of items per page
"""
def search(query, params, offset, per_page=20):
    if DEBUG:
        print "CA SEARCH INITIATING"
    if not query and not params: 
        return Result(0,1),{}

    offset, page = modulate_offset(int(offset), per_page)    
    retrieved_response, args = _url_builder(query, params)
    hits =  _count(retrieved_response)
    next_offset = offset + per_page
    page = offset/per_page +1

    result = Result(hits, next_offset)
    response_json = retrieved_response.json()
    results = response_json["results"]
    for iobject in results:
        thumbnail_url = iobject[PREVIEW_MEDIA]
        original_url = iobject[ORIGINAL_MEDIA]
        title = iobject[TITLE]
        objID = iobject[ID]
        #TODO sort out the source URL

        if DEBUG:
            print "got to images - thumbnail is: " + thumbnail_url

        image = ResultImage(original_url, thumbnail_url, title, objID)
        result.addImage(image)
    return result, args


def _url_builder(query, params):
    """
    builds the url to be used in the search, separate from the "search" method because it allows
    it to be used in the count method. Search needs to return an image list, whereas count can just
    iterate through the search_request josn and count the number of entries
    
    offsets and per_page only matter when returning the actual image, so not needed for this
    """
    #Default search occurring
    #search_request = requests.get(BASE_URL+_build_search(query, params), auth=('administrator', 'c2da32'))
    image_bundles =( '{'
        '"bundles":{'
            '"' +ORIGINAL_MEDIA+ '":{"returnURL":"true"},'
            '"' +PREVIEW_MEDIA+ '":{"returnURL":"true"},'
            '"ca_objects.preferred_labels":true'
        '}'
    '}')
    #TODO: CHANGE AUTHORIZATION FROM ADMIN TO BASE USER WHEN THAT IS FIXED
    # and then to a proper user later on - not sure how that's gonna work, though

    search_url, arguments = _build_search(query, params)
    if DEBUG: 
        print "got past _build_search() " +BASE_URL+ search_url
    search_request = requests.get(BASE_URL + search_url, auth=('administrator', 'c2da32'),
        data = image_bundles )
    if DEBUG:
        print 'PASSED REQUEST'
    if DEBUG and ADVANCED_DEBUG:
        print "Status code for ca search is: " + str(search_request.status_code)
        if search_request:
            print str(search_request.text)
        else:   
            print "search request object is null?"
        
    return search_request, arguments
    


"""
========
URL HELPERS 
========
"""

def _build_search(query, params):
    """return a search query with the given keywords and parameters"""
    if DEBUG:
        print "building search for CA"+ str(params) +"--"+ str(query)
    #PLACEHOLDER -- only searches the objects table and does the simplest
    #search possible for now
    query_terms = params.copy() if( params and params != {} ) else _translate_query(query)
    arguments = _args()
    keywords = ""
    query_string = ""

    if 'query_string' in query_terms:
        query_string = query_terms['query_string']
        arguments.update({'query_string':query_string})
        del query_terms['query_string']
    if 'keywords' in query_terms:
        arguments.update({'keywords':query_terms['keywords']})
        del query_terms['keywords']
    # TODO: need to do all the query string processing here  
    #   but, for now just a simple search assumption will work by default

    if DEBUG: 
        print "query string for CA is now :" + query_string
    if query_string != "":
        keywords += query_string
    
    return "ca_objects?q="+keywords, arguments

"""
=========
GETTERS
=========
"""
def get_logo():
    return LOGO_URL
def get_searcher_page():
    return HOMEPAGE_URL

"""
=========
TOOLS
=========
"""
def _translate_query(query):
    if DEBUG:
        print "translating query " + str(query)
    translator = Query_Language(identifier)
    if DEBUG:
        print 'translator is ' + str(translator)    
    query_terms = translator.searcher_translator(query)
    if DEBUG: 
        print 'query terms are ' + str(query_terms)
    return query_terms
    
def count(query, parameters={}):
    """external count method, needed for searcher to show
        number of hits to the general search mechanism"""
    if DEBUG:
        print "HIT COUNT ON CA"
    if not query or query in "keywords=, params={}":
        return 0
    search_object, args = _url_builder(query, parameters)
    search_object = search_object.json()
    return len(search_object["results"])

def _count(search_request):
    """internal count method, needed to calculate offset, 
        among other things, always use this method when counting 
        hits inside the searcher"""
    search_object = search_request.json()
    return len(search_object["results"]) 

def _args():
    return {"keywords":[]} 

"""
==========
PARAMETERS
==========
"""

parameters = MapParameter({
    "keywords" : ScalarParameter(str, label="keywords")})

