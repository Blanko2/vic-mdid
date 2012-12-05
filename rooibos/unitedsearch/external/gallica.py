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
        first_url, params = build_advanced_url(keywords, params)
    else:
        first_url = build_simple_url(keywords)
    return first_url, params #second_url,params
    
def build_simple_url(keywords):
    keywords = re.sub(" ", "+", keywords)
    return re.sub("QUERY", keywords, BASE_FIRST_SIMPLE_SEARCH_URL)#, re.sub("QUERY", keywords, BASE_SIMPLE_SEARCH_URL)
    
 
def build_sidebar_URL(params):
    copyright   = ""
    languages     = ""
    start_date    = ""
    end_date  = ""
    non_keywords = ["copyright" ,"languages","start date","end date","adv_sidebar"]
    
    if "copyright" in params:
        copyright = getcopyright(params)   
    if "languages" in params:
        languages = getlanguages(params)
    if "start date" in params:
        start_date = getDate(params["start date"])
    if "end date" in params:  
        end_date = getDate(params["end date"])
        
    tmp_params = params
    if "copyright" in params:
        copyright = getcopyright(params)
    if "languages" in params:
        languages = getlanguages(params)
    if "start date" in params:
        start_date = getDate(params["start date"])
    if "end date" in params:  
        end_date = getDate(params["end date"])
    if "or" in params:
        opt_or_map = params["or"]
    if "except" in params:
        opt_not_map = params["except"]
    for key in non_keywords:
        if key in tmp_params:
            del tmp_params[key]
    keywords = []
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
        keywords.append([filter_type_map[first_key],first_value,"MUST"])
    else:
        keywords.append(["f_allcontent","","MUST"])
    
    for key in tmp_params:
        wordlist = tmp_params[key]
        for keyword in wordlist:
            value = keyword[0]
            opt = opt_type_map[keyword[1]]
            if key in filter_type_map:
                filter_type = filter_type_map[key]
            sub_query = [filter_type,value,opt]
            keywords.append(sub_query)
    
    i = 1
    optionals_string=""
    for sub_query in keywords:
        index = str(i)
        optionals_string += "&ope"+index+"="+sub_query[2]+"&catsel"+index+"="+sub_query[0]+"&cat"+index+"="+sub_query[1]
        i=i+1
    
    # shove everything into the url
    replacements = {  
      'START': start_date,
      'SEARCH_FILTERS': optionals_string,
      'END': end_date,
      'LANGUAGES': languages,
      'COPYRIGHT': copyright
     }
    replacer = re.compile('|'.join(replacements.keys()))
    first_url = replacer.sub(lambda m: replacements[m.group(0)], FIRST_ADVANCED_SEARCH_URL_STRUCTURE)
    return first_url, params 
 
def build_advanced_url(keywords, params):
    if "all" in params:
        keywords += " " + getValue(params,"all")
        del params['all']
    #Pulls out five things: Keywords, 2 Dates, copyright and languages, then deletes them from the 
    #  dict and pulls out up to four optional parameters -- all remaining parameters are dumped into
    #  keywords
    copyright     = ""
    languages     = ""
    start_date    = ""
    end_date  = ""
    opt_not_map   = {}       
    if "copyright" in params:
        copyright = getcopyright(params)
        del params['copyright']      
    if "languages" in params:
        languages = getlanguages(params)
        del params['languages']
    if "start date" in params:
        start_date = getDate(params["start date"])
    if "end date" in params:  
        end_date = getDate(params["end date"])
    # deal with remaining optional arguments
    optionals_dict = {}
    keyworded_optionals = {}
    unsupported_parameters = {}
    # grab the "key word" dictionary out of params 
    # merge it with the rest of params
    temp_optionals = {}
    if "key word" in params:
        temp_optionals = getValue(params, "key word")    
        del params['key word']
        temp_optionals, unsupported_parameters = merge_dictionaries(params, temp_optionals, valid_keys )
    else:
        temp_optionals = params
    # dont need params anymore
    for opt_parameter in temp_optionals:
        opt_parameter_tmp = opt_parameter.replace('-','')
        if (opt_parameter in filter_type_map and len(temp_optionals[opt_parameter]) != 0 ):   # supported parameter type and existing value
            if len(optionals_dict) <=4:
                optional_type = filter_type_map[opt_parameter]
                optionals_dict[optional_type] = temp_optionals[opt_parameter]
                if opt_parameter == "not" :
                    key = optional_type = filter_type_map[opt_parameter_tmp]
                    value = temp_optionals[opt_parameter]
                    if isinstance(key,list):
                        key=key[0]
                    if isinstance(value,list):
                        value = value[0]
                    if not key in opt_not_map:
                        opt_not_map.update({key:[value]})
                    else:
                        v = opt_not_map[key]
                        value = v.append[value]
                        opt_not_map.update({key:value})
            else:
                keywords += " " + temp_optionals[opt_parameter]
                keyworded_optionals[opt_parameter] = temp_optionals[opt_parameter]
        elif (opt_parameter_tmp in filter_type_map and len(temp_optionals[opt_parameter]) != 0 and len(optionals_dict) <=4):
            optional_type = filter_type_map[opt_parameter_tmp]
            optionals_dict[optional_type] = temp_optionals[opt_parameter]
            key = optional_type = filter_type_map[opt_parameter_tmp]
            value = temp_optionals[opt_parameter]
            if isinstance(key,list):
                key=key[0]
            if isinstance(value,list):
                value = value[0]
            if not key in opt_not_map:
                opt_not_map.update({key:[value]})
            else:
                v = opt_not_map[key]
                value = v.append[value]
                opt_not_map.update({key:value})
        else:
            if isinstance(temp_optionals[opt_parameter],list):
                keywords += " " + temp_optionals[opt_parameter][0]
                unsupported_parameters[opt_parameter] = temp_optionals[opt_parameter][0]
            else:
                keywords += " " + temp_optionals[opt_parameter]
                unsupported_parameters[opt_parameter] = temp_optionals[opt_parameter]
    
    # start with keywords, than add on any other requested optionals
    start=1
    optionals_string=""
    if keywords.strip() and not keywords.strip()=='':
        start=2
        optionals_string = optionals_string+"&catsel1="+filter_type_map["all"]+"&cat1="+keywords.strip().replace(' ','+')
    # needs to check for the correct input -- dont want to get lists of strings -- need strings!!!
    for i in range(0, len(optionals_dict)):
        index = str(i+start)    # want to index starting at 2, because keywords has already filled cat1
        opt = "MUST"
        key = optionals_dict.keys()[i]
        value = optionals_dict.values()[i]
        if isinstance (value,list):
            value = value[0]
        if key in opt_not_map:
            not_list=opt_not_map[key]
            if value in not_list:
                opt="MUST_NOT" 
        ope="&ope"+index+"="+opt
        optionals_string += ope
        optionals_string += "&catsel"+index+"="+key+"&cat"+index+"="+value 
    # shove everything into the url
    replacements = {    
        'START': start_date,
        'SEARCH_FILTERS': optionals_string,
        'END': end_date,
        'LANGUAGES': languages,
        'COPYRIGHT': copyright
        } 
    replacer = re.compile('|'.join(replacements.keys()))
    first_url = replacer.sub(lambda m: replacements[m.group(0)], FIRST_ADVANCED_SEARCH_URL_STRUCTURE)
    return first_url, optionals_dict #second_url, optionals_dict

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
    return Image(url, params = build_URL(query, pa,
                 image_identifier['url'],
                 image_identifier['thumb'],
                 image_identifier['title'],
                 meta,
                 json_image_identifier))
    
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
 
""" 
=================
PARAMETERS   ##
=================
"""
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
