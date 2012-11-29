""" National Gallery of Australia"""
from rooibos.unitedsearch import *		# other search tools, such as parameter types
from rooibos.unitedsearch.common import *	# methods common to all external searchers
import urllib2					# to get page from url address
from BeautifulSoup import BeautifulSoup		# html scraper


name="National Gallery of Australia"
identifier = "ngaust"

def search(query, params, offset, num_wanted):
    offset = int(offset)
    
    # get 1st page
    url_base = _get_url(query, params)
    html_page = _get_html(url)
    total = _count(html_page)
    
    # deal with there being less images than desired
    if total is 0:
	return Result(0, offset), {}

    num_wanted = total if (total < num_wanted) else num_wanted
    
    # get actual images and add to result
    while (num_images < num_wanted

    # return
    return Result(0, offset), {}

# TODO make more efficient?
def count(query):
    return search(query, {}, 0, 1)[0].total

# TODO
def getImage(image_identifier):
    return None

parameters = MapParameter({
    "aname": OptionalParameter(ScalarParameter(str), "Artist"),
    "title": OptionalParameter(ScalarParameter(str), "Title"),
    "display_order": DefinedListParameter(["artist", "title", "creation date"], label="Display Order")
    })