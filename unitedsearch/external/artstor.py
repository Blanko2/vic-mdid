# TODO remove unused imports
#import urllib, urllib2, time, cookielib, math
import urllib2
#from django.utils import simplejson
#from os import makedirs
#from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
#from rooibos.storage import Storage, Media
#from rooibos.solr.models import SolrIndexUpdates
#from rooibos.solr import SolrIndex
#from rooibos.access.models import AccessControl
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError
from django.conf import settings
#from django.core.urlresolvers import reverse
#from rooibos.federatedsearch.models import FederatedSearch, HitCount
from rooibos.unitedsearch import *
from rooibos.unitedsearch.common import *
from BeautifulSoup import BeautifulSoup
#import cookielib
#import datetime
#import socket
from rooibos.unitedsearch.external.translator.query_language import Query_Language
from rooibos.unitedsearch.external.translator.artstor_dict import query_dict
from rooibos.unitedsearch.external.artstor_parser import parse_parameters

name = "Artstor US"
identifier = "artstor"
HOMEPAGE_URL = "http://www.artstor.org/index.shtml"
LOGO_URL = "http://www.artstor.org/images/global/g-artstor-logo.gif"

""" UNITEDSEARCH VERSION OF ARTSTOR
Heavily based on fedaratedsearch/Artstor code - moved here so all searchers are under common interface
"""

def search(query, params, off, num_results_wanted):
    off = int(off)

    # query and params both come from sidebar, so should have exactly one.
    if not query and not params:
	return Result(0, off), get_empty_parameters()
    elif query and params:
	raise NotImplementedError
    elif query:
	query_terms = Query_Language(identifier).searcher_translator(query)
    else:
	query_terms = parse_parameters(params)
    for key in query_terms:
        query_terms[key] = list_to_str(query_terms[key])
    
    """
    Disable modifiers and adv search for now
    Todo: Work out if artstor can process adv search and modifiers
          Adding Adv sidebar if possible
    """
    
    del_list = []
    for key in query_terms:
        if not key == "":
            del_list.append(key)
    for key in del_list:
        if key in query_terms:
            del query_terms[key]
    
    
    
    if "query_string" in query_terms:
        del query_terms["query_string"]
    # return empty result if no search terms (submitting an empty query breaks artstor)
    if len(query_terms) is 0:
	return Result(0, 0), get_empty_parameters()

    """
    Caching of results, uncomment and fix if supported in other searchers TODO
    cached, created = HitCount.current_objects.get_or_create(
            source=self.get_source_id(), query='%s [%s:%s]' % (keyword, page, pagesize),
            defaults=dict(hits=0, valid_until=datetime.datetime.now() + datetime.timedelta(1)))
    if not created and cached.results:
	return simplejson.loads(cached.results)
    """
    pagesize = num_results_wanted
    url = _get_url(query_terms, pagesize, off)
    #html_page = _get_html_page(url)
    try:
        html_page = _get_html_page(url)
        if not html_page:
            print "ArtStor did not get any data from server, make sure MDID can reach the server through the firewall"
            return Result(0, off), _build_returnable_parameters(query_terms)
        results = ElementTree(file=html_page)
        num_results = int(results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords')) or 0
    except:		# XML parsing error
        print "ArtStor XML parsing error"
        num_results = 0
        if not num_results:		# other type of error or no results found
            return Result(0, off), _build_returnable_parameters(query_terms)

    #pages = int(math.ceil(float(total) / pagesize))

    result = Result(num_results, off+50)
    image_divs = results.findall('.//{info:srw/schema/1/dc-v1.1}dc')
    for div in image_divs:
	(url, thumb, image_identifier, title) = _get_image(div)
	result.addImage(ResultImage(url, thumb, title, image_identifier))
	# TODO cope with full image not actually giving result (timeout error)
	

    return result, _build_returnable_parameters(query_terms)

    
def count(query):
    try:
        results = search(query, {}, "0", 1)[0]
        return results.total
    except:
        return 0


def getImage(image_identifier):
  
  url = '%s?query=dc.identifier="%s"&operation=searchRetrieve&version=1.1&maximumRecords=1&startRecord=1' %(settings.ARTSTOR_GATEWAY, image_identifier)
  
  page = _get_html_page(url)
  info_div = ElementTree(file=page).find('.//{info:srw/schema/1/dc-v1.1}dc')
  (url, thumb, identifier, title) = _get_image(info_div)
  
  meta = {}	# TODO
  
  return RecordImage(url, thumb, title, meta, identifier)

  
# TODO support date once we understand how date ranges are done in Artstor (note, can use dc.date=1894 to find images which were done in exactly 1894, or date range starts or ends with 1894, but not which include 1894 within their range)
parameters = MapParameter({
    "": OptionalParameter(ScalarParameter(str), "Keywords")
    })
"""
    "dc.creator": OptionalParameter(ScalarParameter(str), "Creator"),
    "dc.title": OptionalParameter(ScalarParameter(str), "Title"),
    "dc.subject": OptionalParameter(ScalarParameter(str), "Subject")
"""

    
    
def get_empty_parameters() :
    return {
	"": [],
	"dc.creator": [],
	"dc.title": [],
	"dc.subject": []
    }
    

def _build_returnable_parameters(params):
    returnables = {}
    query_string = ""
    for key in params:
        returnables[key] = list_to_str([params[key]])
        if key == "":
            query_string= query_dict[key]+"="+list_to_str([params[key]])+query_string
        else:
            query_string+=","+query_dict[key]+"="+list_to_str([params[key]])
    
    for unused_key in (set(parameters.parammap)-set(params)):
        returnables[unused_key] = []
    query_string = query_string.replace("keywords=","")
    while query_string.startswith(","):
        query_string = query_string[1:]
    while query_string.endswith(","):
        query_string = query_string[:-1]
    returnables["query_string"]=query_string
    return returnables
	
"""
==============
TOOLS
=============
"""
    
def _get_url(query_dict, pagesize, offset):
    offset = str(int(offset)+1)
    query_string = _build_query_string(query_dict)
    # version from fedaratedsearch/Artstor/search
    url = '%s?query=%s&operation=searchRetrieve&version=1.1&maximumRecords=%s&startRecord=%s' % (
	settings.ARTSTOR_GATEWAY,
	#urllib.quote(query_string),
	query_string,
	pagesize,
	offset,	# because ARTSTOR counts from 1, not 0
    )
    """
    # version from fedaratedsearch/Artstor/hits_count  Why are they different?
    url = '%s?%s' % (
            settings.ARTSTOR_GATEWAY,
            urllib.urlencode([('query', 'cql.serverChoice = "%s"' % query),
                              ('operation', 'searchRetrieve'),
                              ('version', '1.1'),
                              ('maximumRecords', '50')])
        )
        """
    return url

def _build_query_string(query_dict):
    qs = ""
    
    # deal with keywords, as they must go first
    if '' in query_dict:
	qs += "\"" + query_dict[''] + "\"&"
    # then add all other params
    for key in query_dict:
	if not key is '':
	    # append each key value to the string as key="value"
	    qs += key + "=\"" + list_to_str(query_dict[key]) + "\"+and+"


    #remove trailing characters (added in expectation of more parameters)
    if qs.endswith('&'):
	qs = qs.rstrip('&')
    else:
	qs = qs.rstrip('+and+')
	
    # replace all whitespace (this is a url, afterall)
    qs = qs.replace(' ', '+')
    return qs
    
    
def _get_html_page(url):
    opener = proxy_opener()
    try:
	html_page = opener.open(urllib2.Request(url))
	return html_page
    except urllib2.URLError:
	print "ArtStor urllib error"
	return None
    except:
        print "ArtStor url opener exception"
    return None

def get_logo():
    return LOGO_URL

def get_searcher_page():
    return HOMEPAGE_URL

def _get_image(div):
    
    fields = div.findall('{http://purl.org/dc/elements/1.1/}identifier')
    url_regex = re.compile("\?id=(?P<id>.*?)&source")	# get everything between '?id=' and '&source'
    for field in fields:
	if field.text.startswith('URL'):
	    #url = field.text[len('URL:'):].replace('preview.', '')
	    url_id = re.findall(url_regex, field.text)[0]
	    url = "http://library.artstor.org/library/ExternalIV.jsp?objectId="+url_id
	    
	    # TODO, work out why first (commented-out) method gives timeout errors and use instead if possible
	elif field.text.startswith('THUMBNAIL'):
	    thumb = field.text[len('THUMBNAIL:'):]
	else:
	    id = field.text
    title = div.findtext('{http://purl.org/dc/elements/1.1/}title')
    
    return url, thumb, id, title
