"""Flickr searcher updated for the newer MDID version 
uses python-requests as opposed to urllib2
"""
import json
import requests
import rooibos.unitedsearch as unitedsearch 

from rooibos.settings_local import DEBUG, PROXY, FLICKR_KEY, FLICKR_SECRET
from django.conf import settings
from unitedsearch import RecordImage, Result, ResultImage
from unitedsearch import MapParameter, ScalarParameter, OptionalParameter, UserDefinedTypeParameter
from unitedsearch import DefinedListParameter, DoubleParameter, ListParameter
from unitedsearch.common import modulate_offset 
from unitedsearch.external.translator.query_language import Query_Language

name = "Flickr"
identifier = "flickr"
LOGO_URL = "http://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Flickr_wordmark.svg" +\
                               "/120px-Flickr_wordmark.svg.png"
HOMEPAGE_URL="http://flickr.com"

SEARCH_HEAD= "https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key="+FLICKR_KEY
SEARCH_TAIL = "&format=json&nojsoncallback=1"

IMAGE_HEAD= "https://farm"
IMAGE_MID = ".staticflickr.com/"
"""
format for IMAGE_* is 
https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}.jpg ||
https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}_[m|s|t|z|b].jpg ||
https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{o-secret}_[o|b].(jpg|gif|png)

view <a href="https://www.flickr.com/services/api/misc.urls.html">this link</a> for more info
"""

def search(query, params, offset, per_page=20):
    """ external search method, performs the search and builds the results page
        parameters: 
            query - string - query to be performed 
            params - string - parameters coming off sidebar search
            offset - int - offset of results on page vs per_page amount
            per_page - int - # of results per page
        returns: results page
        """
    if DEBUG:
        print "Flickr search initializing"
    if not query and not params:
        return Result(0,1), {}
    
    offset, page = modulate_offset(int(offset), per_page)
    next_offset = offset + per_page
    page = offset/per_page +1 

    retrieved_response, args = _perform_search(query, params, page, per_page)
    hits = _count(retrieved_response)

    result = Result(hits, next_offset)    
    response_json = retrieved_response
    results = response_json["photos"]["photo"]
    
    result_object = _build_result(result, results)
    return result_object, args    
    
def _build_result(result, results):
    """
    Flickr has two basic image types w/ several different sizes available, original image and standard
    original images have an 'original secret' and 'original format property' and allow you to request
    the original size for viewing: '_o'. 
    standard images do not have that, so we request the largest size, 'Large' which is '_b' in the call
    """
    for iobject in results:
        object_id = iobject["id"]
        server_id = iobject["server"]
        secret = iobject["secret"]
        farm_id = str(iobject["farm"])
        title = iobject["title"] 
        owner = iobject["owner"]    
        original_format = None
        original_secret = None
        if 'originalsecret' in results:
            #only need to check if secret is in because then both exist as is original photo
            original_secret = iobject["originalsecret"] 
            original_format = iobject["originalformat"]
        base_url = IMAGE_HEAD + farm_id + IMAGE_MID + server_id + "/" + object_id + '_' 

        original_format = '.' +  original_format if original_format else '.jpg'
        if original_secret and original_format:
            original_url = base_url + original_secret + '_o' + original_format 
        else:
            original_url = base_url + secret + '_b' + original_format
        thumbnail_url = base_url + secret + '_t' + original_format

        image = ResultImage(original_url, thumbnail_url, title, object_id)
        result.addImage(image)
    return result
    

def _perform_search(query, params, page, per_page=20):
    """
    Performs the actual search for Flickr and returns the 
    JSON string as a result
    """
    search_url, arguments = _build_url(query, params, page, per_page)
    search_request = requests.get(search_url)
        
    return search_request.json(), arguments


def _build_url(query, params, page, per_page):
    """
    builds the url for the request to Flickr
    """
    
    query_terms = params.copy() if (params and params != {}) else _translate_query(query)
    arguments = _args()
    keywords = ""
    query_string = ""  
    
    if 'query_string' in query_terms:
        query_string = query_terms['query_string']
        arguments.update({'query_string':query_string})
        del query_terms['keywords']
    if 'keywords' in query_terms:
        arguments.update({'keywords':query_terms['keywords']})
        del query_terms['keywords']

    if query_string != "":
        keywords += query_string +"+"
    
    #for default search &text= X + X

    #flickr has a text and tag search mechanism, need to sort that out at this level
    #   but not going to do that currently so TODO implement more search than just 
    #   at the text level
    pages_value = "&per_page="+str(per_page)+"&page="+str(page)
    url = SEARCH_HEAD +"&text="+ keywords + pages_value + SEARCH_TAIL
    #need to add in 'extra= originalformat'
    if DEBUG:
        print 'url for FLICKR = ' + url
    return url, arguments

"""
===========
GETTERS
===========
"""
def get_logo():
    return LOGO_URL
def get_searcher_page():
    return HOMEPAGE_URL

"""
===========
TOOLS
===========
"""

def _translate_query(query):
    translator = Query_Language(identifier)
    query_terms = translator.searcher_translator(query)
    return query_terms

def _args():
    return {"keywords":[]}

def count(query, parameters={}):
    """
    external count method
    returns: number of hits for search as an integer
    """
    if not query or query in "keywords=, params={}":
        return 0
    
    search_object, args = _perform_search(query, parameters, 1)
    return _count(search_object) 

def _count(retrieved_response):
    """
    internal count method
    returns: number of hits for search as an integer
    """
    hits = int(retrieved_response['photos']['total'])
    return hits 


"""
============
PARAMETERS
============
"""

parameters = MapParameter({
    "keywords" : ScalarParameter(str, label="keywords")})

