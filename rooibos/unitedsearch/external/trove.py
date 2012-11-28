import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser

from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import *   # methods common to all databases
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

name = "Trove"
identifier = "trove"

BASE_URL = "http://trove.nla.gov.au/picture/result?"



def count(query) :
    return 12345

def search(query, params, off, num_wanted) :
    return Result(0, off), {}