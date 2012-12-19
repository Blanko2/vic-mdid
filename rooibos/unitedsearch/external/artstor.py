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
#from rooibos.unitedsearch.external.artstor_parser import parse_parameters

name = "Artstor US"
identifier = "artstor"

""" UNITEDSEARCH VERSION OF ARTSTOR
Heavily based on fedaratedsearch/Artstor code - moved here so all searchers are under common interface
"""
# TODO support parameters
def search(query, params, off, num_results_wanted):
    off = int(off)
    
    print "artstor 34 \n\tquery %s\n\tparams %s" %(query, params)
    # query and params both come from sidebar, so should have exactly one.
    if not query and not params:
	return Result(0, off), get_empty_parameters()
    elif query and params:
	print "artstor 34, shouldn't have reached here... Have both query (%s) and params (%s)" %(query, params)
	raise NotImplementedError
    elif query:
	query_terms = Query_Language(identifier).searcher_translator(query)
    else:
	query_terms = Query_Language(identifier).translate_parameters(params)
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
    html_page = _get_html_page(url)
    try:
	results = ElementTree(file=html_page)
	print BeautifulSoup(html_page)
	print "artstor 60"
	num_results = int(results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords')) or 0
    except ExpatError:		# XML parsing error
	num_results = 0
    if not num_results:		# other type of error or no results found
	return Result(0, off), get_empty_parameters()	# return None?

    #pages = int(math.ceil(float(total) / pagesize))

    result = Result(num_results, num_results+off)
    image_divs = results.findall('.//{info:srw/schema/1/dc-v1.1}dc')
    for div in image_divs:
	(url, thumb, image_identifier, title) = _get_image(div)
	result.addImage(ResultImage(url, thumb, title, image_identifier))
	# TODO cope with full image not actually giving result (timeout error)
    return result, get_empty_parameters()	# TODO parameters!!!

    
def count(query):
    results = search(query, {}, "0", 1)[0]
    return results.total or 0



def getImage(image_identifier):
  
  url = '%s?query=dc.identifier="%s"&operation=searchRetrieve&version=1.1&maximumRecords=1&startRecord=1' %(settings.ARTSTOR_GATEWAY, image_identifier)
  
  page = _get_html_page(url)
  info_div = ElementTree(file=page).find('.//{info:srw/schema/1/dc-v1.1}dc')
  (url, thumb, identifier, title) = _get_image(info_div)
  
  meta = {}	# TODO
  
  return RecordImage(url, thumb, title, meta, identifier)

  
# TODO support date once we understand how date ranges are done in Artstor (note, can use dc.date=1894 to find images which were done in exactly 1894, or date range starts or ends with 1894, but not which include 1894 within their range)
parameters = MapParameter({
    "keywords": OptionalParameter(ScalarParameter(str), "Keywords"),
    "creator": OptionalParameter(ScalarParameter(str), "Creator"),
    "title": OptionalParameter(ScalarParameter(str), "Title"),
    "subject": OptionalParameter(ScalarParameter(str), "Subject")
    })
    
    
def get_empty_parameters() :
    return {
	"keywords": [],
	"creator": [],
	"title": [],
	"subject": []
    }
    

"""
==============
TOOLS
=============
"""

def _parse_parameters(params_dict):
    # TODO
    return {'': "hat"}
    
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
    print "artstor 125 url \n%s\n" %url
    return url

def _build_query_string(query_dict):
    print "artstor 128 query_dict %s" %query_dict
    qs = ""
    
    # deal with keywords, as they must go first
    if '' in query_dict:
	qs += "\"" + query_dict[''] + "\"&"
	del query_dict['']
    # then add all other params
    for key in query_dict:
	# append each key value to the string as key="value"
	qs += key + "=\"" + query_dict[key] + "\"+and+"

    #remove trailing characters (added in expectation of more parameters)
    if qs.endswith('&'):
	qs = qs.rstrip('&')
    else:
	qs = qs.rstrip('+and+')
    return qs
    
    
def _get_html_page(url):
    print "artstor 171 url %s" %url
    opener = proxy_opener()
    try:
	print "artstor 174"
	html_page = opener.open(urllib2.Request(url))
	print "artstor 176 html %s" %BeautifulSoup(html_page)
	return html_page
    except urllib2.URLError:
	return None


def _get_image(div):
    
    fields = div.findall('{http://purl.org/dc/elements/1.1/}identifier')
    for field in fields:
	if field.text.startswith('URL'):
	    url = field.text[len('URL:'):]
	elif field.text.startswith('THUMBNAIL'):
	    thumb = field.text[len('THUMBNAIL:'):]
	else:
	    id = field.text
    title = div.findtext('{http://purl.org/dc/elements/1.1/}title')
    
    return url, thumb, id, title