""" FLICKR IS NOT IMPLEMENTED FULLY IN THE CURRENT VIC-MDID VERSION"""

import json
import requests
import rooibos.unitedsearch as unitedsearch 

from rooibos.settings_local import DEBUG, PROXY, FLICKR_API, FLICKR_SECRET
from django.conf import settings
from rooibos.federatedsearch.flickr import FlickrSearch
from unitedsearch import RecordImage, Result, ResultImage
from unitedsearch import MapParameter, ScalarParameter, OptionalParameter, UserDefinedTypeParameter
from unitedsearch import DefinedListParameter, DoubleParameter, ListParameter
from unitedsearch.common import modulate_offset 

name = "Flickr"
identifier = "flickr"
LOGO_URL = "" 

IMAGE_URL = "https://farm"
IMAGE_MID = ".staticflickr.com/"

def search(query, params, offset, per_page=20):
    if DEBUG:
        print "Flickr search initializing"
    if not query and not params:
        return Result(0,1), {}
    
    offset, page = modulate_offset(int(offset), per_page)
    retrieved_response, args = _perform_search(query, params)
    hits = _count()
    next_offset = offset + per_page
    page = offset/per_page +1 

    

def _perform_search(query, params):
    """
    Performs the actual search for Flickr and returns the 
    JSON string as a result
    """
    search_url, arguments = _build_url(query, params)
    #TODO







def _build_url(query, params):
    """
    builds the url for the request to Flickr
    """
    
    query_terms = params.copy() if (params and params != {}) else _translate_query(query)
    arguments = _args()
    keywords = ""
    query_string = ""  


    #flickr has a text and tag search mechanism, need to sort that out at this level
    #   but not going to do that currently so TODO implement more search than just 
    #   at the text level

"""
===========
GETTERS
===========
"""
def get_logo():
    return LOGO_URL
def get_searcher_homepage():
    return HOMPAGE_URL


def _translate_query(query):
    translator = Query_Language(identifier)
    query_terms = translator.searcher_translator(query)
    return query_terms




def _args():
    return {"keywords":[]}

    """
    so basically the flickr api lets you select a response format - we will use
    Json because it is easier to work with in python than REST
    
    need to form an API call with the given search parameters and then read 
        that call and act on it  
    
    REQUIRED parameters = method (calling method) api_key
    OPTIONAL parameter = format => JSON

    when performing a search, flickr allows a tag or text-based search 
        -- also has a 'tag mode' which allows "OR" or "AND" combinations
            of tags
        -- use this for advanced search behaviour default search should 
            use 'text' however 
    
    FLICKR also has a 'per_page' argument which is useful - default of their is
        100, but we will use 20 as that is our default

    to obtain the photo URL a call can be made with the format specified at 
    https://www.flickr.com/services/api/misc.urls.html    
    
    to get the source information, use flickr.photos.getSizes --    
        -- returns the sizes and given urls for the passed photo
    """
