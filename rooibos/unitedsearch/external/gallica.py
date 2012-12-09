import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser
from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import *   # methods common to all databases
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

# these field names are set by software requirement
name = "Gallica"        # database name the user will recognise
identifier = "gallica"  # identifier for view, urls

BASE_SIMPLE_SEARCH_URL = "http://gallica.bnf.fr/Search?ArianeWireIndex=index&f_typedoc=images&q=QUERY&pageNumber=PAGENUMBER&lang=EN&tri=&n=50&p=PAGEIDX" 
BASE_URL = "http://gallica.bnf.fr"
BASE_FIRST_SIMPLE_SEARCH_URL = "http://gallica.bnf.fr/Search?ArianeWireIndex=index&f_typedoc=images&q=QUERY&n=50&p=PAGEIDX&pageNumber=200000&lang=EN"
#ADVANCED_SEARCH_URL_STRUCTURE = "http://gallica.bnf.fr/Search?idArk=&n=50&p=PAGEIDX&pageNumber=PAGENUMBER&lang=EN&adva=1&adv=1&reset=&urlReferer=%2Fadvancedsearch%3Flang%3DEN&enreg=&tri=SEARCH_FILTERS&date=daTo&daFr=START&daTo=ENDLANGUAGES&t_typedoc=images&dateMiseEnLigne=indexDateFrom&firstIndexationDateDebut=&firstIndexationDateFin=COPYRIGHT&tri=&submit2=Start+search"
FIRST_ADVANCED_SEARCH_URL_STRUCTURE = "http://gallica.bnf.fr/Search?idArk=&n=50&p=PAGEIDX&pageNumber=200000&lang=EN&adva=1&adv=1&reset=&urlReferer=%2Fadvancedsearch%3Flang%3DEN&enreg=&tri=SEARCH_FILTERS&date=daTo&daFr=START&daTo=ENDLANGUAGES&t_typedoc=images&dateMiseEnLigne=indexDateFrom&firstIndexationDateDebut=&firstIndexationDateFin=COPYRIGHT&tri=&submit2=Start+search"
#&dateMiseEnLigne=indexDateFrom

ADVANCED_SEARCH_URL_STRUCTURE = "http://gallica.bnf.fr/Search?idArk=&n=ITEMSPERPAGE&p=PAGENUMBER&lang=EN&adva=1&adv=1&reset=&urlReferer=%2Fadvancedsearch%3Flang%3DEN&enreg=&tri=SEARCH_FILTERS&date=daTo&daFr=START&daTo=ENDLANGUAGES&t_typedoc=images&dateMiseEnLigne=indexDateFrom&firstIndexationDateDebut=&firstIndexationDateFin=COPYRIGHT&tri=&submit2=Start+search"

def count(keyword) :
    first_url, params = build_URL(keyword, {})
    soup = get_search_result_parser(first_url, 1)
    return __count(soup)

def get_search_result_parser(base_url, page_idx) :
    page_url = re.sub("PAGEIDX", str(page_idx),base_url)
    html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(page_url)
    search_results_parser = BeautifulSoup(html)
    return search_results_parser

""" Do the search, return the results and the parameters dictionary used (must have
all parameter types included, even if their value is merely [] - to show up in ui sidebar"""
def search(query, params, off, num_wanted) :
    per_page = __items_per_page(num_wanted)
    off = (int)(off)
    if off<0:
        off=0
    page_idx = 1 + (off/per_page)
    
    images = []
    first_url, params = build_URL(query, params) 
    first_round = True      # optimisation to say we don't need to replace the first search_results_parser
    search_results_parser = get_search_result_parser(first_url, page_idx)
    if not search_results_parser:
        print "Something went horribly wrong, Gallica failed to respond properly, gallica.py ln 46ish in search method"
        return Result(0, off), empty_params
    num_results = __count(search_results_parser)
    num_pages = num_results/per_page + 1
    num_unwanted = off%per_page
    if page_idx>num_pages :
        page_idx = num_pages
        num_unwanted = 0
        off = (num_pages-1)*per_page
        search_results_parser = get_search_result_parser(first_url, page_idx)
    if __count(search_results_parser) is 0:
        return Result(0, off), empty_params
    num_wanted = min(num_wanted, num_results-off)    # how many were asked for mitigated by how many actually existing
    if num_wanted <0 :
        num_wanted =0
    while len(images) < num_wanted:
        if not first_round :
            if page_idx>=num_pages:
                break
            page_idx = page_idx+1
            search_results_parser = get_search_result_parser(first_url, page_idx)
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
    arg = empty_params
    return result, arg
  
"""
=======================
URL BUILDERS
======================
"""
def build_URL(query, params):
    if query=="" and "adv_sidebar" in params: #From side bar
        return build_sidebar_URL(params)
    keywords, para_map = break_query_string(query) 
    params, unsupported_parameters = merge_dictionaries(para_map, params, valid_keys)

    if len(params)!=0:
	  first_url, arg = build_advanced_url(keywords, params)
    else:
	  first_url, arg = build_simple_url(keywords)
    return first_url, params #second_url,params
    
def build_simple_url(keywords):
    arg = get_empty_params()
    arg.update({"simple_keywords":keywords})
    keywords = re.sub(" ", "+", keywords)
    return re.sub("QUERY", keywords, BASE_FIRST_SIMPLE_SEARCH_URL), arg#, re.sub("QUERY", keywords, BASE_SIMPLE_SEARCH_URL)
 
def build_advanced_url(keywords, params):
    if "all" in params:
        keywords += " " + getValue(params,"all")
        del params['all']
    #Pulls out five things: Keywords, 2 Dates, copyright and languages, then deletes them from the 
    #  dict and pulls out up to four optional parameters -- all remaining parameters are dumped into
    #  keywords
    keyword_list = []
    arg = {} #dict contains params with fixed structures for result interface to desplay the query
    arg_list = [] # list contains values for DefinedListParameter:[[field0,value0],[opt1,[field1,value1]],[opt2,[field2,value2]],...]
    arg, params, copyright, language, start_date, end_date = build_arg(params)
    # deal with remaining optional arguments
    optionals_dict = {}
    keyworded_optionals = {}
    # grab the "key word" dictionary out of params 
    # merge it with the rest of params
    temp_params = params
    # dont need params anymore
    for opt_parameter in temp_params:
      fixed_opt_parameter = opt_parameter.replace('-','')
      if fixed_opt_parameter=="not":
          fixed_opt_parameter="all"
      opt = "and"
      if opt_parameter.startswith('-') or opt_parameter=="not":
          opt = "except"
      if fixed_opt_parameter in filter_type_map:
          filter_type = filter_type_map[fixed_opt_parameter]
      else:
          filter_type = filter_type_map["all"]
          fixed_opt_parameter = "all"
      value = temp_params[opt_parameter]
      if isinstance(value, list):
          value = value[0]
      if opt=="except" :
          keyword_list.append([filter_type,value,opt_type_map[opt]])
      else:
          # if opt is "and", adds as the first element
          keyword_list.insert(0,[filter_type,value,opt_type_map[opt]])
    if len(keywords)>0:
       keyword_list.insert(0,[filter_type_map["all"],keywords,opt_type_map["and"]])
    if keyword_list[0][2]=="except":
       keyword_list.insert(0,[filter_type_map["all"],"",opt_type_map["and"]])
    if len(keyword_list)>5:
      keyword_list= merge_keyword_list(keyword_list)
    arg_list = build_arg_list(keyword_list)
    arg.update({"field":arg_list})
    i = 1
    optionals_string=""
    for sub_query in keyword_list:
        index = str(i)
        optionals_string += "&ope"+index+"="+sub_query[2]+"&catsel"+index+"="+sub_query[0]+"&cat"+index+"="+sub_query[1]
        i=i+1
    # shove everything into the url
    replacements = {	
      'START': start_date,
      'SEARCH_FILTERS': optionals_string,
      'END': end_date,
      'LANGUAGES': language,
      'COPYRIGHT': copyright
      }
    replacer = re.compile('|'.join(replacements.keys()))
    first_url = replacer.sub(lambda m: replacements[m.group(0)], FIRST_ADVANCED_SEARCH_URL_STRUCTURE)
    return first_url, arg 

def build_sidebar_URL(params):
    arg = {} #dict contains params with fixed structures for result interface to desplay the query
    keyword_list = [] # list contains [field,value,option] as element 
    non_keywords = ["copyright" ,"language","start date","end date","adv_sidebar"] # parameters outside "field"
    arg, params,copyright, language, start_date, end_date = build_arg(params)
    tmp_params = params
    for key in non_keywords:
        if key in tmp_params:
            del tmp_params[key]
    #TODO REFACTOR
    # Adding the first keyword to keyword_list list (does not contain opt "or" or "except")
    if "first" in tmp_params:
        first_key = tmp_params["first"]
        del tmp_params["first"]
        first_value = tmp_params[first_key][0][0]
        if len(tmp_params[first_key])==1:
            del tmp_params[first_key]
        else:
            l = tmp_params[first_key]
            del l[0]
            tmp_params.update({first_key:l})
        keyword_list.append([filter_type_map[first_key],first_value,"MUST"])
    else:
        keyword_list.append(["f_allcontent","","MUST"])
    for key in tmp_params:
        wordlist = tmp_params[key]
        for keyword in wordlist:
            value = keyword[0]
            opt = opt_type_map[keyword[1]]
            if key in filter_type_map:
                filter_type = filter_type_map[key]
            sub_query = [filter_type,value,opt]
            keyword_list.append(sub_query)
    i = 1
    optionals_string=""
    arg_list = build_arg_list(keyword_list)
    arg.update({"field":arg_list})
    for sub_query in keyword_list:
        index = str(i)
        optionals_string += "&ope"+index+"="+sub_query[2]+"&catsel"+index+"="+sub_query[0]+"&cat"+index+"="+sub_query[1]
        i=i+1
    # shove everything into the url
    replacements = {  
      'START': start_date,
      'SEARCH_FILTERS': optionals_string,
      'END': end_date,
      'LANGUAGES': language,
      'COPYRIGHT': copyright
      }
    replacer = re.compile('|'.join(replacements.keys()))
    first_url = replacer.sub(lambda m: replacements[m.group(0)], FIRST_ADVANCED_SEARCH_URL_STRUCTURE)
    return first_url ,arg


"""
=============
TOOLS
=============
"""
"""
calculate the optimal number of items to display per page,
to minimise the number of html pages to read """
def __items_per_page(num_wanted) :
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
    # example : background-image:url(/resize?w=128&amp;url=http%3A%2F%2Ftools.yoolib.net%2Fi%2Fs1%2Finha%2Ffiles%2F9001-10000%2F9518%2Fmedia%2F9520%2F0944_bensba_est006118_2%2FWID200%2FHEI200.jpg);background-position:center center;background-repeat:no-repeat"
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
    if not soup:
        return 0
    div = soup.find('head').find('title')#.find('meta','title')
    fixed_div = str(div.renderContents()).replace(",","").replace('.','')
    try:
        return (int)(re.findall("\d{1,}", fixed_div)[0])
    except:
        return 0

def __scrub_html_for_property(property_name, html) :
    for para in html.findAll('p') :
        if para.strong and para.strong.renderContents().startswith(property_name) :
            contents = re.findall("(?<=\</strong\>).*", para.renderContents())
            if contents :
                return contents[0]
    return "None"

#Uses by unitedsearch/views.py to select images
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

def add_string(kw, string):
    if string =="":
        return kw
    if kw=="":
        kw += string
    else:
        kw += "+"+string
    return kw

def merge_keyword_list(keyword_list):
    temp_keyword_list = keyword_list
    kw=""
    not_kw=""
    for keyword in keyword_list :
        if keyword[0]==filter_type_map["all"] and keyword[2]==opt_type_map["and"]:
            kw = add_string(kw,keyword[1])
            temp_list.remove(keyword)
        elif keyword[0]==filter_type_map["all"] and keyword[2]==opt_type_map["exept"]:
            not_kw = add_string(not_kw,keyword[1])
            temp_keyword_list.remove(keyword)
    kw_size =0
    not_size=0
    if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
        kw_size =1
    if not not_kw=="":
        not_size=1
    size = len(temp_keyword_list)+kw_size+not_size
    while size>5:
       element = temp_keyword_list.pop()
       if element[2]==opt_type_map["and"]:
           kw = add_string(kw,element[1])
       else:
           not_kw = add_string(not_kw,element[1])
       if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
            kw_size =1
       if not not_kw=="":
            not_size=1
       size = len(temp_keyword_list)+kw_size+not_size  
    if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
       temp_keyword_list.insert(0,[filter_type_map["all"],kw,opt_type_map["and"]])
    if not not_kw=="":
       temp_keyword_list.append([filter_type_map["all"],not_kw,opt_type_map["except"]])


#TODO replace with _
def build_arg(params):
    arg={}
    copyright   = ""
    language     = ""
    start_date    = ""
    end_date  = ""
    if "copyright" in params:
        copyright = getcopyright(params)
        arg.update({"copyright":params["copyright"]})
    else:
        arg.update({"copyright":["All"]})
    if "language" in params:
        language = getlanguages(params)
        arg.update({"language":params["language"]})
    else:
        arg.update({"language":["All"]})
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
    return arg, params , copyright, language, start_date, end_date

"""
return a list contains values for DefinedListParameter:[[field0,value0],[opt1,[field1,value1]],[opt2,[field2,value2]],...]
"""
def build_arg_list(keyword_list):
    arg_list = []
    for keyword in keyword_list:
        if arg_list==[]:
            arg_list.append([filter_reverse_map[keyword[0]],keyword[1]])
        else:
            arg_list.append([opt_reverse_map[keyword[2]],[filter_reverse_map[keyword[0]], keyword[1]]])
    while len(arg_list)<5:
        arg_list.append([])
    return arg_list
    
"""
==============
## GETTERS ##
==============
"""
def getlanguages(params) :
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
    
    if params['languages'] == 'All' :
        lang_string = ""
    else :
        lang_string = "&t_language=" + lang_codes[params['languages']]
    return lang_string

def getcopyright(params) :
    if (not params['copyright']) or (len(params['copyright']) == 0) :
        return ""
    # if reach here, have copyright  
    copyright_codes = {
        "Free": "fayes",
        "Subject to conditions": "fano"
    }
    if params['copyright'] == 'All' :
        copy_string = ""
    else :
        copy_string = "&t_free_access=" + copyright_codes[params['copyright']]
    return copy_string    

def getDate(date):
    return date

def get_empty_params():
    return {"start date": [],
    "end date": [],
    "language": [],
    "copyright": [],
    "all": [],
    "field": [],
    "option": {"opt1":'',"opt2":'',"opt3":'',"opt4":'',"opt5":''}
    }
 
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
# these reverse maps are used to build args for interface to display original query
opt_reverse_map = {
    "SHOULD":"or",
    "MUST":"and",
    "MUST_NOT":"except"
    }
filter_reverse_map = {
  "f_creator":'artist',
  "f_title":'title',
  "f_content":'content' ,
  "f_tdm":'table',
  "f_subject":'subject',
  "f_source":'source',
  "f_metadata":'Bibliographic',
  "f_publisher":'publisher',
  "f_allmetadata":'isbn',
  "f_allcontent":'all',
  '' : "all"  # default so as not to have blank string
  }    
field_types = ["all","artist", "title", "content", "table of contents or captions", "subject", "source", "bibliographic record", "publisher", "isbn"]
option_types = ["and", "or", "except"]   

parameters = MapParameter({
  "start date": OptionalParameter(ScalarParameter(str, "start date")),
  "end date": OptionalParameter(ScalarParameter(str, "end date")),
  "languages": 
  DefinedListParameter(["All", "French", "English", "Italian", "Chinese", "Spanish", "German", "Greek", "Latin"],  multipleAllowed=False, label="Language"),
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
  
empty_params = {"start date": [],
    "end date": [],
    "languages": [],
    "copyright": [],
    "all": [],
    "key word": {"artist":[], "title":[], "content":[], "table of contents or captions":[], "subject":[], "source":[], "bibliographic record":[], "publisher":[], "isbn":[]},
    "field": [],
    "option": {"opt1":'',"opt2":'',"opt3":'',"opt4":'',"opt5":''}
}

valid_keys=["start date",
    "end date",
    "languages",
    "copyright",
    "all",    
    "artist",
    "title",
    "content",
    "table Of contents or captions",
    "subject",
    "source",
    "bibliographic record",
    "publisher",
    "isbn",
    "not"]
