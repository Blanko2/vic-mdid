import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser

from rooibos.unitedsearch import *              # other search tools
from rooibos.unitedsearch.common import * 	# methods common to all databases
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

# these field names are set by software requirement
name = "Gallica"        # database name the user will recognise
identifier = "gallica"  # identifier for view, urls


BASE_SIMPLE_SEARCH_URL = "http://gallica.bnf.fr/Search?ArianeWireIndex=index&f_typedoc=images&q=QUERY&pageNumber=PAGENUMBER&lang=EN&tri=&n=ITEMSPERPAGE" 
BASE_URL = "http://gallica.bnf.fr"

ADVANCED_SEARCH_URL_STRUCTURE = "http://gallica.bnf.fr/Search?idArk=&n=ITEMSPERPAGE&p=PAGENUMBER&lang=EN&adva=1&adv=1&reset=&urlReferer=%2Fadvancedsearch%3Flang%3DEN&enreg=&tri=SEARCH_FILTERS&date=daTo&daFr=START&daTo=ENDLANGUAGES&t_typedoc=images&dateMiseEnLigne=indexDateFrom&firstIndexationDateDebut=&firstIndexationDateFin=COPYRIGHT&tri=&submit2=Start+search"

#&dateMiseEnLigne=indexDateFrom

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
  '' : "f_creator"	# default so as not to have blank string
  } # note, table is table of contents or Captions
  
"""# # # # # # # # # # #
# # # # # TOOLS # # # # #
"""# # # # # # # # # # #

"""
URL BUILDERS

"""
def build_URL(query, params):
    keywords, para_map = break_query_string(query) 
    params, unsupported_parameters = merge_dictionaries(para_map, params, valid_keys)
    print "params here"
    print params
    #check if simple or advanced search
    print "para_map in build_URL:"
    print para_map
    if len(params)!=0:
      url, params = build_advanced_url(keywords, params)
    else:
      url = build_simple_url(keywords)
    return url, params
	
	
def build_simple_url(keywords):
    keywords = re.sub(" ", "+", keywords)
    return re.sub("QUERY", keywords, BASE_SIMPLE_SEARCH_URL)
    
    
def build_advanced_url(keywords, params):
  print "params in build_advanced_url"
  print params
  if "all" in params:
    keywords += " " + getValue(params,"all")
    del params['all']
  #Pulls out five things: Keywords, 2 Dates, copyright and languages, then deletes them from the 
  #  dict and pulls out up to four optional parameters -- all remaining parameters are dumped into
  #  keywords
  
  copyright 	= ""
  languages 	= ""
  start_date 	= ""
  end_date 	= ""
  
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
  print 'Temp Optionals ==========================================================' 
  print params
  print temp_optionals 

  for opt_parameter in temp_optionals:
      if (opt_parameter in filter_type_map and len(temp_optionals[opt_parameter]) != 0 ): 	# supported parameter type and existing value
	  if len(optionals_dict) < 4:		# can only support 4 optional parameters. Damn gallica
	    optional_type = filter_type_map[opt_parameter]
	    optionals_dict[optional_type] = temp_optionals[opt_parameter]
	  else:
	    keywords += " " + temp_optionals[opt_parameter]
	    keyworded_optionals[opt_parameter] = temp_optionals[opt_parameter]
      else:
	print temp_optionals[opt_parameter]
	keywords += " " + temp_optionals[opt_parameter][0]
	unsupported_parameters[opt_parameter] = temp_optionals[opt_parameter]
	
  # start with keywords, than add on any other requested optionals
  optionals_string = "&catsel1="+filter_type_map["all"]+"&cat1="+keywords.strip()
  
  # needs to check for the correct input -- dont want to get lists of strings -- need strings!!!
  print optionals_dict
  
  
  for i in range(0, len(optionals_dict)):
    index = str(i+2)	# want to index starting at 2, because keywords has already filled cat1
    optionals_string += "&ope"+index+"=MUST"+"&catsel"+index+"="+optionals_dict.keys()[i]+"&cat"+index+"="+optionals_dict.values()[i][0]
  
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
  
  return url, optionals_dict
"""    
def get_optional_search_filters(params) :
    
    para = params["key word"]
    filters_string = ""
    for i in range(1,6) :
      index = (str)(i)
      field_type = para['filter_'+index][0]
      field_type_for_url = filter_type_map[field_type]
      print field_type + ": " + field_type_for_url + "\n\n"
      field_value = para['filter_'+index][1]
      
      if i != 1:
	filters_string += "&ope"+index+"=MUST"
      
      filters_string += "&catsel"+index+"="+field_type_for_url+"&cat"+index+"="+field_value
      
    return filters_string
    
def buildParams() :
  p = {'languages': None, 'end date': [], 'start date': [], 'copyright': None, 'key word': {'filter_5': ['', ''], 'filter_4': ['', ''], 'filter_3': ['', ''], 'filter_2': ['', ''], 'filter_1': ['', '']}}
  
  
  for idx in para_map :
    key = para_map[idx].keys()[0]
    value = para_map[idx][key]
    value = value.replace(' ','+')
    filterIdx = 'filter_'+str(idx)
    
    if key=='keywords' :
      entry = ['all', value ]
      (p['key word'])[filterIdx] = entry
    elif key=='title_t' :
      entry = ['title', value]
      (p['key word'])[filterIdx] = entry
    elif key=='creator_t' :
      entry = ['artist', value]
      (p['key word'])[filterIdx] = entry
    elif key=='source_t' :
      entry = ['source', value]
      (p['key word'])[filterIdx] = entry
    elif key=='publisher_t' :
      entry = ['publisher', value]
      (p['key word'])[filterIdx] = entry
    elif key=='date_t' :
      p['end date'] = value
  print p
  return p
  
def haveParams() :
  return not query is None
"""  


  
def __get_search_resultsHtml(url, first_index_wanted, items_per_page) :
     # calculate page number and items
    
    page_num = str(1 + (first_index_wanted/items_per_page))
    url = re.sub("ITEMSPERPAGE", str(items_per_page), re.sub("PAGENUMBER", page_num, url))
    
    html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
    unwanted = first_index_wanted%items_per_page
    print url
    return (html,unwanted)

    
def any_results(html_page_parser) :
    
    results_div = html_page_parser.find('div', 'ariane')
    text = results_div.findAll('span')[1].next.strip()	# find the bit of text that says if results\
    
    return text != "No result"
    
    
def __items_per_page(num_wanted) :
    """ calculate the optimal number of items to display per page,
    to minimise the number of html pages to read """
    
    # based on the options the site itself offers
    if num_wanted <= 15 :
        return 15
    elif num_wanted <= 30 :
        return 30
    else :
        return 50
    
   
   
def __create_image(soup, id_div) :


#    url_block = titre_div.findNext('a')
#    
#    url_containing_string = url_block['href']
#    regex_for_url = re.compile(".*?(?=\.r=)")
#    url_base = regex_for_url.findall(url_containing_string)
#    
#    if no url_base :    # image not available to site
    
    
    # find relevant parts of html
    url_block = id_div.findNext('span', 'imgContner')
    description_block = url_block.findNext('div', 'titre')
    
    

    # extract wanted info
    image_id = id_div.renderContents();
    
    url_containing_string = url_block['style']
    
    # images in gallica are stored in 2 main ways, so deal with each of these separately then have a default for all others
    
    # case 1 : ark images
    # example url_containing_string: 
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
    
    image_identifier = json.dumps(
                                 {'url': url,
                                'thumb' : thumb,
                                'title': title,
                                'src_url': description_block.findNext('a')['href'],
                                'descriptive_html': description_block.findNext('div', 'notice').renderContents()
                                })
                                 
    
    return ResultImage(url, thumb, title, image_identifier)
    
     

def __count(soup) :
    if not soup:
      return 0
    fragment = soup.find('div', 'fonctionBar2')
    if not fragment:
      return 0
    div = fragment.find('div', 'fonction1')
    fixed_div = str(div.renderContents()).replace(",","")
    return (int)(re.findall("\d{1,}", fixed_div)[0])



def __scrub_html_for_property(property_name, html) :
    
    for para in html.findAll('p') :
        if para.strong and para.strong.renderContents().startswith(property_name) :
            contents = re.findall("(?<=\</strong\>).*", para.renderContents())
            if contents :
	      return contents[0]
            
    
    return "None"
    

def getImage(json_image_identifier) :
    
    image_identifier = json.loads(json_image_identifier)
    descriptive_parser = BeautifulSoup(image_identifier['descriptive_html'])
    
    meta = {'title': image_identifier['title'],
            'author': __scrub_html_for_property("Author", descriptive_parser),
            #'date': __scrub_html_for_property("Date", descriptive_parser),
            #'access': __scrub_html_for_property("copyright", descriptive_parser)
            }
    
    return Image(url, params = build_URL(query, pa,
                 image_identifier['url'],
                 image_identifier['thumb'],
                 image_identifier['title'],
                 meta,
                 json_image_identifier))
    
    
def count(keyword) :
      url, params = build_URL(keyword, {})
      html, unwanted = __get_search_resultsHtml(url, 0, 50)
      search_results_parser = BeautifulSoup(html)
      #print "html in count\n"+html
      return __count(search_results_parser)

""" Do the search, return the results and the parameters dictionary used (must have
all parameter types included, even if their value is merely [] - to show up in ui sidebar"""
def search(query, params, off, num_wanted) :
  
  
    print "query"
    print query
    print "params"
    print params
    perPage = num_wanted
    off = (int)(off)
    
    images = []
    
    url, params = build_URL(query, params)
    #html, unwanted = __get_search_resultsHtml(url, off, __items_per_page(perPage))
    #search_results_parser = BeautifulSoup(html)
    #num_results = __count(search_results_parser)
    #num_wanted = min(num_wanted, num_results-off)    # how many were asked for mitigated by how many actually existing
    
    
    print "DEBUGGING SEARCH\n\n"
    print "URL: "+url
    print "params: "+str(params)
    print "query: "+str(query)
    html, unwanted = __get_search_resultsHtml(url, off, __items_per_page(perPage)) #Do it again because num_wanted has been changed
    search_results_parser = BeautifulSoup(html)
    #print "html in search\n"+str(html)
    #print "search_resultts_parser = " + str(search_results_parser)
    num_results = __count(search_results_parser)
    num_wanted = min(num_wanted, num_results-off)    # how many were asked for mitigated by how many actually existing
    
    
    if not any_results(search_results_parser) :
      return Result(0, off), empty_params
      
    
    first_round = True      # optimisation to say we don't need to replace the first search_results_parser
    
    
    while len(images) < num_wanted :
        
        if not first_round :
	    html, unwanted2 = __get_search_resultsHtml(url, off+len(images), __items_per_page(perPage))
            search_results_parser = BeautifulSoup(html)
        else :
            first_round = False
            
            
        # find start points for image data
        image_id_divs = search_results_parser.findAll('div', 'resultat_id')
        
        if unwanted>0:
	  while unwanted>0:
	    unwanted = unwanted-1
	    del image_id_divs[0]
        
        
        # build images
        for div in image_id_divs :
            images.append(__create_image(search_results_parser, div))
        
         
        # discard any excess
        
            #field_types = ["artist", "title", "content", "table of contents or captions", "subject", "source", "bibliographic record", "publisher", "isbn", "all"]    
        
    if len(images) > num_wanted :
            while len(images) > num_wanted :
                images.pop()
    
    # wrap in Result object and return
    result = Result(num_results, off+len(images))
    for image in images :
        result.addImage(image)
        
    # and make sure params contains all param types
    params, unsupported_parameters = merge_dictionaries(params, empty_params, valid_keys)
    return result, params
  
  
##         ##
## GETTERS ##
##         ##

def getlanguages(params) :
    if not params['languages'] or len(params['languages']) == 0 :
      #params['languages'] = 'All'
      #return "&t_language="
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
      #params['copyright'] = 'All'
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
  
##      	##
## PARAMETERS 	##
##      	##
  
"""
DOESNT DO MUCH RIGHT NOW BUT IT WILL BE A BIG BOY I PROMISE.
... LAZY GIT TODO
"""
def getDate(date):
  return date
  

## 		##
## PARAMETERS 	##
## 		##
field_types = ["artist", "title", "content", "table of contents or captions", "subject", "source", "bibliographic record", "publisher", "isbn"]
    
parameters = MapParameter({
  "start date": OptionalParameter(ScalarParameter(str, "start date")),
  "end date": OptionalParameter(ScalarParameter(str, "end date")),
  "languages": 
  DefinedListParameter(["All", "French", "English", "Italian", "Chinese", "Spanish", "German", "Greek", "Latin"],  multipleAllowed=False, label="Language"),
  "copyright": 
  DefinedListParameter(["All", "Free", "subject to conditions"], label="copyright"),
  "key word" : MapParameter({
    "artist": UserDefinedTypeParameter(field_types),
    "title": UserDefinedTypeParameter(field_types),
    "content": UserDefinedTypeParameter(field_types),
    "table of contents or captions": UserDefinedTypeParameter(field_types),
    "subject": UserDefinedTypeParameter(field_types),
    "source": UserDefinedTypeParameter(field_types),
    "bibliographic record": UserDefinedTypeParameter(field_types),
    "publisher": UserDefinedTypeParameter(field_types),
    "isbn": UserDefinedTypeParameter(field_types)
    })
  })
  
empty_params = {"start date": [],
    "end date": [],
    "languages": [],
    "copyright": [],
    "all": [],
    "key word": {"artist":[], "title":[], "content":[], "table of contents or captions":[], "subject":[], "source":[], "bibliographic record":[], "publisher":[], "isbn":[]}
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
    "isbn"]
