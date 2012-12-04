# TODO remove unused imports
import urllib, urllib2, time, cookielib, math
from django.utils import simplejson
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
from rooibos.solr import SolrIndex
from rooibos.access.models import AccessControl
from xml.etree.ElementTree import ElementTree
from xml.parsers.expat import ExpatError
from django.conf import settings
from django.core.urlresolvers import reverse
from rooibos.federatedsearch.models import FederatedSearch, HitCount
from rooibos.unitedsearch import *
from rooibos.unitedsearch.common import *
from BeautifulSoup import BeautifulSoup
import cookielib
import datetime
import socket

name = "Artstor US"
identifier = "artstor"

""" UNITEDSEARCH VERSION OF ARTSTOR
Heavily based on fedaratedsearch/Artstor code - moved here so all searchers are under common interface
"""
# TODO support parameters, parameterised query
def search(query, params, off, num_results_wanted):
    
    off = int(off)
    if not query:
            return None
    """
    Caching of results, uncomment and fix if supported in other searchers TODO
    cached, created = HitCount.current_objects.get_or_create(
            source=self.get_source_id(), query='%s [%s:%s]' % (keyword, page, pagesize),
            defaults=dict(hits=0, valid_until=datetime.datetime.now() + datetime.timedelta(1)))
    if not created and cached.results:
	return simplejson.loads(cached.results)
    """
    pagesize = 50
    
    keywords, para_map = break_query_string(query)
    params, unsupported_parameters = merge_dictionaries(para_map, params, parameters.parammap.keys())
    add_to_dict(params, "all words", keywords)
    
    url = _get_url(keywords, params, pagesize, off)
    html_page = _get_html_page(url)
    
    try:
	results = ElementTree(file=html_page)
	num_results = results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords') or 0
    except ExpatError:		# XML parsing error
	num_results = 0
    if not num_results:		# other type of error or no results found
	return Result(0, off), {}	# return None?

    #pages = int(math.ceil(float(total) / pagesize))

    result = Result(num_results, num_results+off)
    #result = dict(records=[], hits=total)
    for image in results.findall('//{info:srw/schema/1/dc-v1.1}dc'):
	for ids in image.findall('{http://purl.org/dc/elements/1.1/}identifier'):
	    if ids.text.startswith('URL'):
		url = ids.text[len('URL:'):]
	    elif ids.text.startswith('THUMBNAIL'):
		tn = ids.text[len('THUMBNAIL:'):]
	    else:
		id = ids.text
	title = image.findtext('{http://purl.org/dc/elements/1.1/}title')
	result.addImage(url, thumb_url, title, {})
	# TODO make sure url, thumb_url are accurate and always exist, make actual image identifier, rather than {}
	"""result['records'].append(dict(
	    thumb_url=tn,
	    title=title,
	    record_url=url))"""

    """cached.results = simplejson.dumps(result, separators=(',', ':'))
    cached.save()"""
    return result, {}	# TODO parameters!!!


def _get_url(query, params, pagesize, offset):
    query = "cat"
    offset = str(int(offset)+1)
    # version from fedaratedsearch/Artstor/search
    url = '%s?query="%s"&operation=searchRetrieve&version=1.1&maximumRecords=%s&startRecord=%s' % (
	settings.ARTSTOR_GATEWAY,
	urllib.quote(query),
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
   
   

def _get_html_page(url):
    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookielib.CookieJar()),
				  urllib2.ProxyHandler({"http": "http://localhost:3128"}))
				  # TODO, use SmartRedirectHandler() from FedaratedSearch/Artstor/__init__.py ?
    """
    #socket.setdefaulttimeout(self.timeout)
    html_page = opener.open(url)
    print "artstor us l111 page %s" %(BeautifulSoup(html_page))
    return html_page
    """
    try:
	html_page = opener.open(urllib2.Request(url))
	return html_page
    except urllib2.URLError:
	return None

# TODO - make this always return count - returning 12345 is to make artstor enterable from search page in ui
def count(query):
    count = search(query, {}, "0", 1)[0].total 
    return count if count > 0 else 12345

# TODO
def getImage(image_identifier):
  return None

# TODO
parameters = MapParameter({})