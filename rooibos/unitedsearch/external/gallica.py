import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser
#from unitedsearch import *                      # other search tools
from rooibos.unitedsearch import *

import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

# these field names are set by software requirement
name = "Gallica"        # database name the user will recognise
identifier = "gallica"  # identifier for view, urls


BASE_SIMPLE_SEARCH_URL = "http://gallica.bnf.fr/Search?ArianeWireIndex=index&f_typedoc=images" # append &q=query&pageNumber=number&lan
BASE_URL = "http://gallica.bnf.fr"

ADVANCED_SEARCH_URL_STRUCTURE = "http://gallica.bnf.fr/Search?idArk=&n=15&p=1&lang=EN&adva=1&adv=1&reset=&urlReferer=%2Fadvancedsearch%3Flang%3DEN&enreg=&tri=SEARCH_FILTERS&date=daTo&daFr=START&daTo=ENDLANGUAGES&t_typedoc=images&dateMiseEnLigne=indexDateFrom&firstIndexationDateDebut=&firstIndexationDateFin=COPYRIGHT&tri=&submit2=Start+search"

#&dateMiseEnLigne=indexDateFrom

filter_type_map = {
  'Artist' : "f_creator",
  'Title': "f_title",
  'Content': "f_content",
  'Table' : "f_tdm",
  'Subject': "f_subject",
  'Source': "f_source",
  'Bibliographic': "f_metadata",
  'Publisher': "f_publisher",
  'IBSN': "f_allmetadata",
  'All': "f_allcontent",
  '' : "f_creator"	# default so as not to have blank string
  } # note, Table is Table of Contents or Captions
  
def get_optional_search_filters(params) :
    
    para = params["Key Word"]
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
    
    
def __get_search_resultsHtml(term, params, first_index_wanted, items_per_page) :
    
    # calculate page number and items
    page_num = str(1 + (first_index_wanted/items_per_page))
    
    def haveSimplePara() :
      term_str = str(term)
      if term_str=="" :
	return False
      return True
    
    def haveParams() :
      return not query is None
      
    if  haveSimplePara() :
	# simple search
	url = BASE_SIMPLE_SEARCH_URL + "&q=" + term + "&pageNumber=" + page_num + "&lang=EN&tri=&n=" + str(items_per_page)
	
    else :
	# advanced search
	def getValue(dict_val):
	    try:
	      r = str(dict_val[0])
	    except IndexError:
	      r = ""
	    if isinstance(r, str): return r
	    return ""
	    #return (str)(dict_val[0])
	    
	def getLanguages() :
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

	def getCopyright() :
	  
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

	      
	replacements = {	
	  'START': getValue(params['start date']),
	  'SEARCH_FILTERS': get_optional_search_filters(params),
	  'END': getValue(params['end date']),
	  'LANGUAGES': getLanguages(),
	  'COPYRIGHT': getCopyright()
	  }
	
	replacer = re.compile('|'.join(replacements.keys()))
	url = replacer.sub(lambda m: replacements[m.group(0)], ADVANCED_SEARCH_URL_STRUCTURE)
	
    html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
    
    return html

    
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
    div = soup.find('div', 'fonctionBar2').find('div', 'fonction1')
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
            #'access': __scrub_html_for_property("Copyright", descriptive_parser)
            }
    
    return Image(
                 image_identifier['url'],
                 image_identifier['thumb'],
                 image_identifier['title'],
                 meta,
                 json_image_identifier)
    
    
def count(term) :
    return __count(__get_search_resultsHtml(term, {}, 0))
    

def search(term, params, off, num_wanted) :
    
    off = (int)(off)
    
    images = []
    search_results_parser = BeautifulSoup(__get_search_resultsHtml(term, params, off, __items_per_page(num_wanted)))
    if not any_results(search_results_parser) :
      return Result(0, off)
      
    num_results = __count(search_results_parser)
    num_wanted = min(num_wanted, num_results)    # how many were asked for mitigated by how many actually exist
    first_round = True      # optimisation to say we don't need to replace the first search_results_parser
    
    
    while len(images) < num_wanted :
        
        
        
        if not first_round :
            search_results_parser = BeautifulSoup(__get_search_resultsHtml(term, params, off+len(images), __items_per_page(num_wanted)))
        else :
            first_round = False
            
            
        # find start points for image data
        image_id_divs = search_results_parser.findAll('div', 'resultat_id')
         
        # discard any excess
        if len(image_id_divs) > num_wanted :
            while len(image_id_divs) > num_wanted :
                image_id_divs.pop()
                
        # build images
        for div in image_id_divs :
            images.append(__create_image(search_results_parser, div))
    
    
    # wrap in Result object and return
    result = Result(num_results, off+len(images))
    for image in images :
        result.addImage(image)
    return result
    
    
    
field_types = ["Artist", "Title", "Content", "Table of contents or captions", "Subject", "Source", "Bibliographic Record", "Publisher", "IBSN", "All"]
    
parameters = MapParameter({
  "start date": OptionalParameter(ScalarParameter(str, "Start Date")),
  "end date": OptionalParameter(ScalarParameter(str, "End Date")),
  "languages": 
  DefinedListParameter(["All", "French", "English", "Italian", "Chinese", "Spanish", "German", "Greek", "Latin"],  multipleAllowed=False, label="Language"),
  "copyright": 
  DefinedListParameter(["All", "Free", "Subject to conditions"], label="Copyright"),
  "Key Word" : MapParameter({
    "filter_1": UserDefinedTypeParameter(field_types, label="Filter 1"),
    "filter_2": UserDefinedTypeParameter(field_types, label="Filter 2"),
    "filter_3": UserDefinedTypeParameter(field_types, label="Filter 3"),
    "filter_4": UserDefinedTypeParameter(field_types, label="Filter 4"),
    "filter_5": UserDefinedTypeParameter(field_types, label="Filter 5")
    })
  })
