import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser
#from rooibos.settings_local import TROVE_KEY
from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import *   # methods common to all databases
from rooibos.settings_local import *
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures
from rooibos.unitedsearch.external.translator.query_language import Query_Language 
from rooibos.unitedsearch.external.trove_parser import parse_trove_query
from rooibos.unitedsearch.image_finder import get_image_url, get_thumble

name = "Trove"
identifier = "trove"

LOGO_URL=""
TROVE_URL = "http://trove.nla.gov.au"
BASE_URL = "http://trove.nla.gov.au/picture/result?"
API_URL = "http://api.trove.nla.gov.au/result?key=TROVE_KEY&zone=picture&q="
BASE_SEARCH_URL = "http://trove.nla.gov.au/picture/result?FIELDSDATEFORMAT&s=OFFSET"
PER_PAGE = 20 #how many results trove actually has per page - can't change this
#LOGO_URL = "http://trove.nla.gov.au/static/37451/img/trove-logo-v2.gif"
LOGO_URL = "http://trove.nla.gov.au/general-test/files/2012/01/API-light.png"
#LOGO_URL = "http://trove.nla.gov.au/general-test/files/2012/01/API-dark.png"
"""
TODO: DELETE THE API KEY AFTER DEVELOPMENT,
get a key associated with the university
"""
TROVE_KEY = "ot2eubi7h2ef5qjn"
api = True
TROVE_DEBUG = False

"""API technical docs:
http://trove.nla.gov.au/general/api-technical
"""
def count(query) :
    if not query or query in "keywords=, params={}":
        return 0
    url,arg = build_URL(query, {})
    if url.endswith("&q=&s=OFFSET"):
        return 0
    search_result_parser = get_search_result_parser(url, 1, 0)
    return _count(search_result_parser)

def _count(soup):
    num=0
    #TODO: api or html
    if api:
        result = soup.find("records")["total"]
        num = int(result)
    else:
        result = soup.find("div", attrs={'id':"pictures"}).find("div", attrs={'class':"hdrresult"}).find("strong")
        if not result:
            result = soup.find("div", attrs={'id':"pictures"}).find("div", attrs={'class':"hdrresult"}).find("b")
        num = int(re.sub("[^0-9]+", "", result.text))
    #print "trove.py, _count, number of results string: "+str(num)
    return num


    
def search(query, params, off, num_wanted) :
    try:
        if (not query or query in "keywords=, params={}") and (not params or params=={}):
            return Result(0, off), empty_params
        off = int(off) #just in case
    
        url, arg = build_URL(query, params)
        if url.endswith("&q=&s=OFFSET"):
            return Result(0, off), arg
        search_result_parser = get_search_result_parser(url, off, 100)#100 max per page
        total = _count(search_result_parser)
        num_wanted = min(num_wanted, total - off)#make sure we're not trying to get too many images
        result = [];
        #TODO: api or html
        while num_wanted>0:
            images = parse_api_results(search_result_parser)

            #now images is all images found on page
            num_got = len(images)
            for i in images:
                if num_wanted > 0:
                    if i[1] not in "":#has thumbnail
                        result.append(i)
                        num_wanted -= 1
                    off+=1#move the offset
            if len(images) is (100 if api else PER_PAGE) and num_wanted > 0:#not last page of results
                #maybe wait here to be nice to trove's servers
                search_result_parser = get_search_result_parser(url, off, 100)#get next page, remember off is modified in loop above
    
        img_list = Result(total, off)
        #print result[0]
        for image in result:
        
            img_list.addImage(ResultImage(image[0], image[1], image[2], image[3]))
        #res = dict(empty_params)
        #res["all words"] = kw
        return img_list, arg
        #return Result(0, off), empty_params
    except:
        # Trove does not accept query contains empty keywords. In that case it causes HTTP Error 500
        return Result(0, off), arg()
    
def parse_api_results(soup):
    images = []
    works = soup.findAll("work")

    for work in works:
        id = work["id"]
        thumbTag = work.find("identifier", attrs={'linktype':'thumbnail'})
        imageTag = work.find("identifier", attrs={'linktype':'fulltext'})
        troveTag = work.find("troveurl")
        if not thumbTag or thumbTag=="":
            thumbTag = imageTag
        if thumbTag:
            thumb = str(thumbTag.string).replace("&amp;", "&")
            thumb = get_thumble(thumb)
        else:
            thumb= "../../../../static/images/thumbnail_unavailable.png"
            #thumb= settings.STATIC_DIR + "/images/thumbnail_unavailable.png"
        
        if imageTag:
            image = str(imageTag.string).replace("&amp;", "&")
        else:
            image = troveTag.string
        #if thumbTag:
        #    thumb = thumbTag.text.replace("&amp;", "&")
        """
        if not thumb:
            text = work.find("identifier", attrs={'linktype':'fulltext'})
            thumb = text.text.replace("&amp;", "&") if text else None
        if not thumb:
            trove = work.find("troveUrl")
            thumb = trove.text.replace("&amp;", "&") if trove else None
        """
        """
        if thumb and not thumb == "":
            image = thumb
            #thumb = get_image_from_thumb(thumb)
            #thumbnail is full image as attempted by get_image_from_thumb
            #link is to the original thumbnail so we can see what went wrong
            if not thumb:
                thumb = "../../../../static/images/thumbnail_unavailable.png"
                #this image source is not implemented, but didn't fail
        else:
            thumb = "../../../../static/images/nothumbnail.jpg"
            image=None
            #thumbnail wasn't included in the data we got from api
            text = work.find("identifier", attrs={'linktype':'fulltext'})
            image = text.text.replace("&amp;", "&") if text else None
            if not image:
                trove = work.find("troveurl")
                image = trove.text.replace("&amp;", "&") if trove else None
                #at worst, this should take you to troveUrl
                if not image:
                    print "\n\n\n\n\n\n\n\nSomething went horribly wrong in trove.py, no troveUrl in record:"
                    print "work:\n"+str(work)
        """
        desc = ""
        descId = work.find("title")
        if descId:
            desc = descId.text
        descId = work.find("contributor")
        if descId and desc in "":
            desc += "\n"+descId.text
        descId = work.find("troveurl")
        if descId and desc in "":
            desc += "\n"+descId.text
        data={'image':image, 'thumb':thumb, 'desc':desc, 'troveid':str(id)}
        #if thumb is not "":
        image = get_image_url(image, thumb)
        images.append([image, thumb, desc, json.dumps(data)])
    return images




def build_URL(query, query_terms):
    if not query_terms:
        query_language = Query_Language(identifier)
        query_terms = query_language.searcher_translator(query)    
    
    url = API_URL.replace("TROVE_KEY", TROVE_KEY)
    arg = empty_arg()
    url, arg = parse_trove_query(url, query_terms,arg)
    return url, arg

        
"""
Feed an assembled url into here, with the offset, and get a parser for 20 results
"""
def get_search_result_parser(base_url, offset, per_page) :
    page_url = re.sub("OFFSET", str(offset),base_url)
    if api:
        page_url += "&n="+str(per_page)
    #page_url = "http://api.trove.nla.gov.au/result?key="+TROVE_KEY+"&zone=picture&q=cat"
    print "trove.py, get_search_result_parser, page_url = "+page_url

    #TODO: replace this with a WORKING html library retrieval
    if TROVE_DEBUG:
        if api:
            f = open("/u/students/novikovech/mdidtestpages/result.xml")
        else:
            f = open("/u/students/novikovech/mdidtestpages/result.html")
        html = ""
        for line in f:
            html += line
    else:
        #html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(page_url)
        opener = proxy_opener()
        html = opener.open(page_url)
    #html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(page_url)
    #print html
    search_results_parser = BeautifulSoup(html)
    #print "trove.py, get_search_result_parser returns  a soup: "+str(search_results_parser is not None)
    return search_results_parser








"""
Required, accessed by external method to select images
"""
def getImage(datastring):
    print datastring.__class__
    data = json.loads(datastring) if isinstance(datastring, unicode) or isinstance(datastring, str) else datastring
    print "get image from : "+str(data)
    thumb = data.get("thumb")
    image = data["image"]
    desc = data["desc"]
    meta = {'creator':'somebody'}#use data['troveid'] to find the metadata using the api?
    i = RecordImage(image, thumb, desc, meta, json.dumps(data))
    #img = RecordImage(url, thumb, name, meta, identifier)
    #print "Constructed image: "+str(img)
    return i





def get_logo():
    return LOGO_URL
def get_searcher_page():
    return TROVE_URL
"""
Check if given param is valid or under different name(creator=artist, etc), return as empty param (keyword) if not
"""
def get_param(param):
    if param in synonyms.keys():
        return synonyms[param]
    return ""


field_types = ["keyword","creator", "title", "subject","isbn","issn","language"]
option_types = ["all of the words", "any of the words", "the phrase", "none of the words"]   

"""
PARAMMAP
"""
parameters = MapParameter({
    "start year": OptionalParameter(ScalarParameter(str)),
    "end year": OptionalParameter(ScalarParameter(str)),
    "availability": DefinedListParameter(["Online", "Access conditions", "Freely available"],  multipleAllowed=False, label="Availability"),
    "field" : ListParameter([
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        ),
        DoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
        UserDefinedTypeParameter(field_types)
        )
        ],label="Keywords")
    })


def empty_arg():
    return {
    "keyword": [],
    "exact phrase": [],
    "exclude words": [],
    "creator": [],
    "title": [],
    "subject": [],
    "isbn": [],
    "issn": [],
    "publictag": [],
    #"access": [],
    "start year": [],
    "end year": [],
    "availability":[],
    "language":[],
    "field" :[]
        }
    
valid_keys = empty_params = {"keyword": [],
    "exact phrase": [],
    "exclude words": [],
    "creator": [],
    "title": [],
    "subject": [],
    "isbn": [],
    "issn": [],
    "publictag": [],
    #"access": [],
    "start year": [],
    "end year": [],
    "availability":[],
    "language":[],
    "field" :[]
    }

synonyms = {"keyword": "",
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