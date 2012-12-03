import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser

from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import *   # methods common to all databases
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

name = "Trove"
identifier = "trove"

BASE_URL = "http://trove.nla.gov.au/picture/result?"
BASE_SEARCH_URL = "http://trove.nla.gov.au/picture/result?FIELDSDATEFORMAT&s=OFFSET"
PER_PAGE = 20 #how many results trove actually has per page - can't change this


def count(query) :
    url = build_URL(query)
    search_result_parser = get_search_result_parser(url, 0)
    return 12345#_count(search_result_parser)

def _count(soup):
    result = search_result_parser.find("div", attrs={'class':"island box primary picture"}).find("strong")
    num = int(re.sub("[^0-9]+", "", result.text))
    print "trove.py, _count, number of results string: "+str(num)
    return num


    
def search(query, params, off, num_wanted) :
    url = build_URL(query)
    search_result_parser = get_search_result_parser(url, off)
    print "trove.py, search, has search_result_parser: "+str(search_result_parser is not None)
    results = search_result_parser.findAll("li", attrs={'class':re.compile("draggableResult")}, limit=20) #results double up after 20
    for result in results:
        print "\n\n\n\n\ntrove.py found record:"
        #print result.prettify()
        
        #"""
        title_block = result.find("dt")
        if title_block:
            title = title_block.text
        else:
            title=""#where else can we find the title?
        print "Title = " + title
        description = title_block.find("a")['href']
        print "Description url = "+description if description else "None"
        id = int(re.findall("[0-9]+", description)[0]) if description else 0
        print "Image id = "+str(id)
        print ".\n.\n.\n."
        creator = result.find("dd", attrs={'class' : "creator"})
        print "Creator = " + (creator.text if creator else "N/A")
        kw = result.find("dd", attrs={'class' : "keywords"})
        print "Keywords = " + (kw.text if kw else "N/A")
        online = result.find("dd", attrs={'class' : "online singleholding"})
        print "Online = " + (online.text if online else "N/A")
        print "Online URL = " + str((online.find("a")['href'] if online else "N/A") or "No link")
        thumbdd = result.find("dd", attrs={'class' : "thumbnail"})
        thumba = thumbdd.find("a") if thumbdd else None
        thumbimg = thumba.find("img") if thumba else None
        thumb = thumbimg['src'] if thumbimg else ""
        print "Thumbnail image src = "+str(thumb)
        #"""
    print "trove.py, search, found a page with "+str(len(results))+" results"
    img_list = Result(0, off)
    return Result(0, off), empty_params

def parse_results(soup):
    return []
    
def build_URL(query):
    print "trove.py, build_URL( "+query+" )"
    fields_string=""
    fields = {}
    year_from = year_to = None
    keywords, para_map = break_query_string(query)
    print "trove.py, build_URL, query = "+query
    print "trove.py, build_URL, keywords = "+keywords
    print "trove.py, build_URL, para_map = "+str(para_map)
    #params, unsupported_parameters = merge_dictionaries(para_map, params, valid_keys)
    for key in para_map.keys():
        print "trove.py, build_URL, for key in para_map.keys loop, key = "+key+", value = "+para_map[key]
        if key in "start_date":
            print "trove.py, build_URL, start date found, and is "+para_map[key]
            year_from = int(para_map[key])
            del(para_map[key])
        elif key in "end_date":
            print "trove.py, build_URL, end date found, and is "+para_map[key]
            year_to = int(para_map[key])
            del(para_map[key])
        else:
            param = get_param(key)#if key is valid(or synonym) param is it's correct name for trove, otherwise key is unsupported and param is "" (keyword)
            if param is "":#key unsupported
                keywords += " "+para_map[key]
            else:
                fields[param] = para_map[key]# fields will now contain all supported parameters and their values
    id=0
    if keywords:
        fields_string += build_field(id, "", "all", keywords.strip().replace(" ", "+").replace("++", "+"))
        id += 1
    for key in fields.keys():
        fields_string += build_field(id, key, "all", fields[key])
        id+=1

    url = BASE_SEARCH_URL.replace("FIELDS", fields_string)
    url = url.replace("DATE", build_date(year_from, year_to))
    url = url.replace("FORMAT", "")
    return url
    

def build_field(id, field, f_type, term):
    print "trove.py, build_field("+str(id)+", "+field+", "+f_type+", "+term+")"
    amp = ""
    if id > 0:
        amp = "&"
    if field is "all words":
        field = ""
    if field and field is not "":
        field = field + "%3A"
    return amp+"q-field"+str(id)+"="+field+"&q-type"+str(id)+"="+f_type+"&q-term"+str(id)+"="+term

def build_date(year_from, year_to):
    print "trove.py, build_date("+str(year_from)+", "+str(year_to)+")"
    if not year_from:
        if not year_to:
            return "" #no date entered
        return "" # let's not bother with those who don't enter start year TODO: maybe we can auto set start since end is actually set
    if not year_to: #start year is set, but not end year
        year_to = 3000
    return "&q-year1-date="+str(year_from)+"&q-year2-date="+str(year_to)
        
"""
Feed an assembled url into here, with the offset, and get a parser for 20 results
"""
def get_search_result_parser(base_url, offset) :
    page_url = re.sub("OFFSET", str(offset),base_url)
    print "trove.py, get_search_result_parser, page_url = "+page_url

    #TODO: replace this with a WORKING html library retrieval
    f = open("/u/students/novikovech/mdidtestpages/result.html")
    html = ""
    for line in f:
        html += line

    #print html
    #html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(page_url)
    search_results_parser = BeautifulSoup(html)
    print "trove.py, get_search_result_parser returns  a soup: "+str(search_results_parser is not None)
    return search_results_parser

















"""
Check if given param is valid or under different name(creator=artist, etc), return as empty param (keyword) if not
"""
def get_param(param):
    if param in synonyms.keys():
        return synonyms[param]
    return ""



    
"""
PARAMMAP
"""
parameters = MapParameter({
    "all words": OptionalParameter(ScalarParameter(str)),
    "exact phrase":OptionalParameter(ScalarParameter(str)),
    "exclude words": OptionalParameter(ScalarParameter(str)),
    "creator": OptionalParameter(ScalarParameter(str)),
    "title": OptionalParameter(ScalarParameter(str)),
    "subject": OptionalParameter(ScalarParameter(str)),
    "isbn": OptionalParameter(ScalarParameter(str)),
    "issn": OptionalParameter(ScalarParameter(str)),
    "publictag": OptionalParameter(ScalarParameter(str)),
    "start date": OptionalParameter(ScalarParameter(str)),
    "end date": OptionalParameter(ScalarParameter(str)),
    "access": OptionalParameter(ScalarParameter(str))
    })

valid_keys = empty_params = {"all words": [],
    "exact phrase": [],
    "exclude words": [],
    "creator": [],
    "title": [],
    "subject": [],
    "isbn": [],
    "issn": [],
    "publictag": [],
    "access": [],
    "start date": [],
    "end date": []
    }

synonyms = {"all words": "",
    "creator" : "creator",
    "author" : "creator",
    "artist" : "creator",
    "photographer" : "creator",
    "painter" : "creator",
    "title" : "title",
    "subject" : "subject",
    "isbn" : "isbn",
    "issn" : "issn",
    "tag" : "publictag",
    "publictag" : "publictag",
    "access" : "access",
    "copyright" : "access",
    }