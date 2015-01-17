"""
Gallica searcher -- voted most likely to break

Because Gallica has several idiosyncracies and works on an HTML scraper,
this searcher is the most likely to break at some point.
Things to note:
    Gallica accepts a maximum of 5 advanced parameters and one of them is
     (in our implementation) always keywords 
     so really it accepts 4 + keywords
    
    Anything to do with BeautifulSoup is HTML scraping/parsing
    
    Searcher coming in from the sidebar are parsed in gallica_parser.py 
        this is the same as in all searchers, but Gallica's is quite 
        persnicketty

    
""" 
import re                                       # regular expressions
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures
from BeautifulSoup import BeautifulSoup         # html parser
from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import proxy_opener   # methods common to all databases
from gallica_parser import parse_gallica
from rooibos.unitedsearch.external.translator.query_language import Query_Language 
from rooibos.unitedsearch.external.translator.query_mod import query_mods
from rooibos.unitedsearch.external.translator.gallica_dict import query_dict
# these field names are set by software requirement
name = "Gallica"        # database name the user will recognise
identifier = "gallica"  # identifier for view, urls

LOGO_URL = "http://gallica.bnf.fr/images/dynamic/perso/logo_gallica.png"
BASE_URL = "http://gallica.bnf.fr"
BASE_SIMPLE_SEARCH_URL = "http://gallica.bnf.fr/Search?ArianeWireIndex=index&f_typedoc=images&q=QUERY&n=50&p=PAGEIDX&pageNumber=200000&lang=EN"
ADVANCED_SEARCH_URL_STRUCTURE = "http://gallica.bnf.fr/Search?idArk=&n=50&p=PAGEIDX&pageNumber=200000&"\
                                    "lang=EN&adva=1&adv=1&reset=&urlReferer=%2Fadvancedsearch%3Flang%3DEN&enreg=&tri=SEARCH_FILTERS&date=daTo&daFr=START"\
                                    "&daTo=ENDLANGUAGES&t_typedoc=images&dateMiseEnLigne=indexDateFrom&"\
                                    "firstIndexationDateDebut=&firstIndexationDateFin=COPYRIGHT&tri=&submit2=Start+search"

def count(keyword) :
    if not keyword or keyword in "keywords=, params={}":
        return 0
    url, arg = build_URL(keyword,{})
    if not url:
        return 0
    soup = get_search_result_parser(url, 1)
    return __count(soup)

def get_search_result_parser(base_url, page_idx) :
    page_url = re.sub("PAGEIDX", str(page_idx),base_url)
    opener = proxy_opener()
    html = opener.open(page_url)#urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(page_url)
    search_results_parser = BeautifulSoup(html)
    return search_results_parser

def search(query, params, off, num_wanted) :
    try:
        """ Do the search, return the results and the parameters dictionary used (must have
        all parameter types included, even if their value is merely [] - to show up in ui sidebar"""
        per_page = __items_per_page(num_wanted)
        off = (int)(off)
        if off<0:
            off=0
        page_idx = 1 + (off/per_page)
        
        images = []
        url, arg = build_URL(query, params) 
        if not url:
            return Result(0, off), arg
        first_round = True      # optimisation to say we don't need to replace the first search_results_parser
        search_results_parser = get_search_result_parser(url, page_idx)
        if not search_results_parser:
            return Result(0, off), arg
        num_results = __count(search_results_parser)
        num_pages = num_results/per_page + 1
        num_unwanted = off%per_page
        if page_idx>num_pages :
            page_idx = num_pages
            num_unwanted = 0
            off = (num_pages-1)*per_page
            search_results_parser = get_search_result_parser(url, page_idx)
        if __count(search_results_parser) is 0:
            return Result(0, off), arg
        num_wanted = min(num_wanted, num_results-off)    # how many were asked for mitigated by how many actually existing
        if num_wanted <0 :
            num_wanted =0
        while len(images) < num_wanted:
            if not first_round :
                if page_idx>=num_pages:
                    break
                page_idx = page_idx+1
                search_results_parser = get_search_result_parser(url, page_idx)
            else :
                first_round = False
            # find start points for image data
            image_id_divs = search_results_parser.findAll('div', 'resultat_id')
            while num_unwanted>0:
                num_unwanted = num_unwanted-1
                del image_id_divs[0]
            # build images
            for div in image_id_divs :
                images.append(__create_image(search_results_parser, div))
            # discard any excess
        if len(images) > num_wanted :
                while len(images) > num_wanted :
                    images.pop()
        # wrap in Result object and return
        result = Result(num_results, off+len(images))
        for image in images :
            result.addImage(image)
        # and make sure params contains all param types

        return result, arg

    except:
        return Result(0, off), get_empty_params()
"""
=======================
URL BUILDERS
======================
"""
def build_URL(query, params):
    """ determines if the url should be simple or advanced and launches
    corresponding method"""
    if query and not params:
        ql = Query_Language(identifier)
        
        
        params = ql.searcher_translator(query)
    query, params = parse_gallica(params)
    if not query and not params:
        return None, get_empty_params()
    if query :
        return build_simple_url(query)
    return build_advanced_url(params)
    
def build_simple_url(keywords):
    arg = get_empty_params()
    if keywords=="":
        return None, arg
    arg.update({"simple_keywords":keywords})
    keywords = re.sub(" ", "+", keywords)
    return re.sub("QUERY", keywords, BASE_SIMPLE_SEARCH_URL), arg#, re.sub("QUERY", keywords, BASE_SIMPLE_SEARCH_URL)
 
def build_advanced_url(params):
    arg = {} #dict contains params with fixed structures for result interface to desplay the query
    
    arg_list = [] # list contains values for DefinedListParameter:[[field0,value0],[opt1,[field1,value1]],[opt2,[field2,value2]],...]
    arg, params, copyright, languages, start_date, end_date = _build_arg(params)
    keyword_list = params["query_list"]
    arg_list = _build_arg_list(keyword_list)
    arg.update({"field":arg_list})
    i = 1
    optionals_string=""
    for sub_query in keyword_list:
        index = str(i)
        filter_type = filter_type_map[sub_query[0]]
        value = sub_query[1]
        opt = opt_type_map[sub_query[2]]
        if not isinstance(value,list):
            value = [value]
        for v in value:        
            optionals_string += "&ope"+index+"="+opt+"&catsel"+index+"="+filter_type+"&cat"+index+"="+v
            i=i+1
            index = str(i)
    # shove everything into the url
    replacements = {	
      'START': start_date,
      'SEARCH_FILTERS': optionals_string,
      'END': end_date,
      'LANGUAGES': languages,
      'COPYRIGHT': copyright
      }
    replacer = re.compile('|'.join(replacements.keys()))
    url = replacer.sub(lambda m: replacements[m.group(0)], ADVANCED_SEARCH_URL_STRUCTURE)
    url = url.replace(' ','+')
    return url, arg 


"""
=============
TOOLS
=============
"""
def __items_per_page(num_wanted) :
    """ calculate the optimal number of items to display per page,
    to minimise the number of html pages to read """
    # based on the options the site itself offers
    return 50

def __create_image(soup, id_div) :
    # find relevant parts of html
    url_block = id_div.findNext('span', 'imgContner')
    description_block = url_block.findNext('div', 'titre')
    # extract wanted info
    image_id = id_div.renderContents();
    url_containing_string = url_block['style']
    # images in gallica are stored in 2 main ways, so deal with each of these separately then have a default for all others
    # case 1 : ark images
    # example url_containing_string:     if '=' in query and params == {}:
    # background-image:url(/ark:/12148/btv1b84304008.thumbnail);background-position:center center;background-repeat:no-repeat
    regex_result = re.search("(?<=background-image:url\()(?P<url>.*)(?P<extension>\..*)\)", url_containing_string)
    if regex_result.group('extension') == '.thumbnail' :
        thumb = BASE_URL + regex_result.group('url') + regex_result.group('extension')
        url = BASE_URL + regex_result.group('url') + '.highres'
    # case 2 : tools.yoolib images
    # example : background-image:url(/resize?w=128&amp;url=http%3A%2F%2Ftools.yoolib.net%2Fi%2Fs1%2Finha%2Ffiles% +
        #2F9001-10000%2F9518%2Fmedia%2F9520%2F0944_bensba_est006118_2%2FWID200%2FHEI200.jpg);
        #background-position:center center;background-repeat:no-repeat"
    elif regex_result.group('url').startswith("/resize") :
        # replace special char values with the actual characters, then strip off the resize part at the start.
        thumb = regex_result.group('url').replace("%3A", ":").replace("%2F", "/").split("url=",1)[1] + regex_result.group('extension')
        # url has set width and height, we set to 2000x2000 here to allow scaling. Last replace is to get fullsize images from buisante.parisdescrates, shouldn't affect any from other sources
        url = re.sub("WID\d*?(?=/)", "WID2000", re.sub("HEI\d*?(?=\.)", "HEI2000", thumb)).replace("/pt/", "/zoom/")
    # case 3: anything else
    else :
        # if external image, won't be thumbnail, treat url and thumbnail as same
        thumb = BASE_URL + regex_result.group('url') + regex_result.group('extension')
        url = thumb
    title = description_block.findNext('a')['title']
    image_identifier = json.dumps({'url': url,
                                'thumb' : thumb,
                                'title': title,
                                'src_url': description_block.findNext('a')['href'],
                                'descriptive_html': description_block.findNext('div', 'notice').renderContents()
                                })
    return ResultImage(url, thumb, title, image_identifier)

def __count(soup) :
    """if it has received an html soup it looks for where the number of results is written out
    if it cannot find it - ie: Gallica has thrown an error due to not finding hits - it will
    return 0 hits"""
    if not soup:
        return 0
    div = soup.find('head').find('title')#.find('meta','title')
    fixed_div = str(div.renderContents()).replace(",","").replace('.','')
    try:
        title_counter = re.findall("\d{1,}", fixed_div)
        count = (int)(title_counter[len(title_counter)-1])
        if count >=0 :
            return count
        else:
            return 0
    except:
        return 0

def __scrub_html_for_property(property_name, html) :
    for para in html.findAll('p') :
        if para.strong and para.strong.renderContents().startswith(property_name) :
            contents = re.findall("(?<=\</strong\>).*", para.renderContents())
            if contents :
                return contents[0]
    return "None"

#Used by unitedsearch/views.py to select images
def getImage(json_image_identifier) :
    image_identifier = json.loads(json_image_identifier)
    descriptive_parser = BeautifulSoup(image_identifier['descriptive_html'])
    meta = {'title': image_identifier['title'],
            'author': __scrub_html_for_property("Author", descriptive_parser),
            }
    return RecordImage(
                 image_identifier['url'],
                 image_identifier['thumb'],
                 image_identifier['title'],
                 meta,
                 json_image_identifier)

    image_identifier = json.loads(json_image_identifier)
    descriptive_parser = BeautifulSoup(image_identifier['descriptive_html'])
    
    meta = {'title': image_identifier['title'],
            'author': __scrub_html_for_property("Author", descriptive_parser),
            }
    return RecordImage(url, params = build_URL(query, pa,
                 image_identifier['url'],
                 image_identifier['thumb'],
                 image_identifier['title'],
                 meta,
                 json_image_identifier))

def _build_arg(params):
    """ Builds the argument dictionary for the sidebar parameters""" 
    arg={}
    copyright  = ""
    languages  = ""
    start_date = ""
    end_date   = ""
    if "query_string" in params:
        arg.update({"query_string":fix_query_string(str(params["query_string"]))})
        del params["query_string"]
    else:
        keywords = ""
        mod_keywords = ""
        queries = ""
        mod_quries = ""
        if "copyright" in params:
            if not queries=="":
                queries += ","
            queries += query_dict["copyright"]+"="+params["copyright"]
   
        if "languages" in params:
            if not queries=="":
                queries += ","
            queries += query_dict["languages"]+"="+params["languages"]

        if "start date" in params:
            if not queries=="":
                queries += ","
            queries += query_dict["start date"]+"="+params["start date"]

        if "end date" in params:  
            if not queries=="":
                queries += ","
            queries += query_dict["end date"]+"="+params["end date"]
  
        if "query_list" in params:
            keyword_list = params["query_list"]
            for sub_query in keyword_list:
                filter_type = filter_type_map[sub_query[0]]
                value = sub_query[1]
                opt = opt_type_map[sub_query[2]]
                if filter_type=="f_allcontent":
                    if opt == "MUST":
                        if isinstance(value,list):
                            for v in value:
                                if mod_keywords != "":
                                    mod_keywords += ","
                                mod_keywords += query_dict[opt]+v
                        else:
                            if keywords != "":
                                keywords += " "
                            keywords += value
                    else:
                        if not isinstance(value,list):
                            value = [value]
                        for v in value:
                            if mod_keywords != "":
                                mod_keywords += ","
                            mod_keywords += query_dict[opt]+v
                else:
                    if mod_quries != "":
                        mod_quries += ","
                    if isinstance (value, list):
                        for v in value:
                            if mod_quries != "":
                                    mod_quries += ","
                            mod_quries += query_dict[opt]+query_dict[filter_type]+"="+v
                    else:
                        mod_quries += query_dict[opt]+query_dict[filter_type]+"="+value
        query_string = keywords+","+mod_keywords+","+mod_quries+","+queries
        query_string = query_string.replace(",,",",")
        while query_string.startswith(","):
            query_string = query_string[1:]
        arg["query_string"] = fix_query_string(query_string)
        
    
    if "copyright" in params:
        copyright = getcopyright(params)
        arg.update({"copyright":params["copyright"]})
    else:
        arg.update({"copyright":["All"]})
    if "languages" in params:
        languages = getlanguages(params)
        arg.update({"languages":params["languages"]})
    else:
        arg.update({"languages":["All"]})
    if "start date" in params:
        start_date = getDate(params["start date"])
        arg.update({"start date":params["start date"]})
    else :
        arg.update({"start date":[]})
    if "end date" in params:  
        end_date = getDate(params["end date"])
        arg.update({"end date":params["end date"]})
    else :
        arg.update({"end date":[]})
    return arg, params , copyright, languages, start_date, end_date

def _build_arg_list(keyword_list):
    """ return a list contains values for 
    DefinedListParameter:[[field0,value0],[opt1,[field1,value1]],[opt2,[field2,value2]],...]
    """
    arg_list = []
    for keyword in keyword_list:
        value = keyword[1]
        if not isinstance(value,list):
            value = [value]
        for v in value:
            if arg_list == []:
                arg_list.append([keyword[0], v])
            else:
                arg_list.append([keyword[2],[keyword[0], v]])
    while len(arg_list)<5:
        arg_list.append([])
    return arg_list
    
"""
==============
## GETTERS ##
==============
"""
def getlanguages(params) :
    """ Unintuitively gets languages that may be in params """
    if not params['languages'] or len(params['languages']) == 0 :
        return ""
    # if reach here, have languages to read, read them  
    lang_codes = {
        "French": "fre",
        "English": "eng",
        "Italian": "ita",
        "Chinese": "chi",
        "Spanish": "spa",
        "German": "ger",
        "Greek": "grc",
        "Latin": "lat"
        }
    value = params['languages']
    if isinstance (value,list):
        value = value[0]
    if value == 'All' :
        lang_string = ""
    elif  value in lang_codes:
        lang_string = "&t_languages=" + lang_codes[value]
    else:
        lang_string = ""
    # Todo: Enable languages
    return ""

def getcopyright(params) :
    """ Checks if copyright is in params and if so, returns it"""
    if (not params['copyright']) or (len(params['copyright']) == 0) :
        return ""
    # if reach here, have copyright  
    copyright_codes = {
        "Free": "fayes",
        "subject to conditions": "fano"
    }

    value = params['copyright']
    if isinstance(value,list):
        value = value[0]
    if value == 'All' :
        copy_string = ""
    else :
        copyright_str = value
        if isinstance(copyright_str,list):
            copyright_str=copyright_str[0]
        if copyright_str in copyright_codes:
            copy_string = "&t_free_access=" + copyright_codes[copyright_str]
        else:
            copy_string = ""
    return copy_string    

def get_logo():
    """ returns the searcher logo - to be placed in the search page"""
    return LOGO_URL
def get_searcher_page():
    """ returns the searcher homepage - to make the logo be a link"""
    return BASE_URL

def getDate(date):
    """OBSOLETE"""
    return date

def get_empty_params():
    return {"start date": [],
    "end date": [],
    "languages": [],
    "copyright": [],
    "all": [],
    "field": []
    }

def fix_query_string(query_string):
    for mod in query_mods:
        if (mod+"=") in query_string:
            query_string = query_string.replace((mod+"="),mod)
        if (mod+"keywords=") in query_string:
            query_string = query_string.replace((mod+"keywords="),mod)
    return query_string
    
""" 
=================
PARAMETERS   ##
=================
"""

# optional categories that can be searched by in the url
# Gallica only allows 5 options at once, thus we consider one of those
# to always be 'Keywords'
filter_type_map = {
  'artist' : "f_creator",
  'title': "f_title",
  'content': "f_content",
  'table' : "f_tdm",
  'subject': "f_subject",
  'source': "f_source",
  'Bibliographic': "f_metadata",
  'publisher': "f_publisher",
  'isbn': "f_allmetadata",
  'all': "f_allcontent",
  'not': "f_allcontent",
  '' : "f_creator"	# default so as not to have blank string
  } # note, table is table of contents or Captions
opt_type_map = {
    'or' : "SHOULD",
    'and' : "MUST",
    'except' : "MUST_NOT"
    }

field_types = ["all","artist", "title", "content", "table of contents or captions", "subject", "source", "bibliographic record", "publisher", "isbn"]
option_types = ["and", "or", "except"]   

parameters = MapParameter({
  "start date": OptionalParameter(ScalarParameter(str, "start date")),
  "end date": OptionalParameter(ScalarParameter(str, "end date")),
  #"languages": 
  #DefinedListParameter(["All", "French", "English", "Italian", "Chinese", "Spanish", "German", "Greek", "Latin"],  multipleAllowed=False, label="Language"),
  "copyright": 
  DefinedListParameter(["All", "Free", "subject to conditions"], label="copyright"),
  "field" : ListParameter([
    UserDefinedTypeParameter(field_types),
    OptionalDoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
    UserDefinedTypeParameter(field_types)),
    OptionalDoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
    UserDefinedTypeParameter(field_types)),
    OptionalDoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
    UserDefinedTypeParameter(field_types)),
    OptionalDoubleParameter(DefinedListParameter(option_types,  multipleAllowed=False, label=""),
    UserDefinedTypeParameter(field_types))
    ])
  })
  

