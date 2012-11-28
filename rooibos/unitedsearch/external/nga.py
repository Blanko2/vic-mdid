from BeautifulSoup import BeautifulSoup      # html parser
import urllib2                               # fetch html
import re                                   # regular expressions
from rooibos.unitedsearch import *       # other website search parts
import json                                 # tool for encoding and decoding complex structures to/from string
from rooibos.unitedsearch.common import *

"""
Searcher for the National Gallery of Art website
"""


BASE_SIMPLE_SEARCH_URL = "https://images.nga.gov/?service=search&action=do_quick_search"
BASE_ADVANCED_SEARCH_URL = "https://images.nga.gov/en/search/show_advanced_search_page/?service=search&action=do_advanced_search&language=en&form_name=default"
BASE_IMAGE_PROPERTIES_URL = "https://images.nga.gov/en/asset/show_zoom_window_popup.html"
BASE_IMAGE_LOCATION_URL = "https://images.nga.gov/?service=asset&action=show_preview&asset"
BASE_THUMBNAIL_LOCATION_URL = "https://images.nga.gov/"

# These variable names are fixed by the software requirements
name = "National Gallery of Art"    # database name that user will recognise
identifier = "nga"            # don't know what this is

  
  

    
def build_parameters(query, params):
    # build parameters dictionary to search by
    """
    print "NGA build_parameters"
    print "query"
    print query
    print "params"
    print params
    """
    keywords, para_map = break_query_string(query)
    """
    print "after break query string"
    print keywords
    print para_map
<<<<<<< HEAD
    
    valid_keys = parameters.parammap.keys()
    params, unsupported_parameters = merge_dictionaries(para_map, params, valid_keys)
    add_to_dict(params, "all words", keywords)

    # get the parameter values to put into the url

    print "Params now-------------------------------------\n\n"
=======
    """
    params, unsupported_parameters = merge_dictionaries(para_map, params, parameters.parammap.keys())
    add_to_dict(params, "all words", keywords)

    # get the parameter values to put into the url
    """
    print "Params\n\n"
>>>>>>> ed04b86c9967486f3d6f6aaf9002f6862bf69c29
    print params
    """

    all_words = getValue(params, 'all words')
    exact_phrase = getValue(params, 'exact phrase')
    exclude = getValue(params, 'exclude words')
    not_in = getValue(params,'not')
    if exclude and not_in:
      exclude += "+"+not_in
    elif not_in:
      exclude = not_in
    if exclude:
        params.update({"exclude words":[exclude]})

    artist = getValue(params, 'artist')
    keywords = getValue(params, 'title')

    accession_number = getValue(params, 'accession number')
    school = getValue(params, 'school')
    classification = getValue(params, 'classification')
    medium = getValue(params, 'medium')
    year1 = getValue(params, 'start date')
    year2 = getValue(params, 'end date')
    access = getValue(params, 'access')


    # build up the url
    url_base = BASE_ADVANCED_SEARCH_URL + "&all_words="+all_words + "&exact_phrase="+exact_phrase+ "&exclude_words="+exclude

    url_base += "&artist_last_name="+artist+"&keywords_in_title="+keywords + "&accession_num="+accession_number

    url_base += "&school="+school + "&classification="+classification + "&medium=" + medium + "&year="+year1 + "&year2="+year2

    url_base += "&open_access="+access

    # replace all whitespace from the parameters
    url_base = re.sub(" ", "+", url_base)

    return params, unsupported_parameters, url_base
    

def __getHTMLPage_Containing_SearchResult(url_base, index_offset) :
  

  
    # set up fields for any type of search
    #print "NGA"
    search_results_per_page = 25
    search_page_num = str(1 + (index_offset/search_results_per_page))   
    howFarDownThePage = index_offset % search_results_per_page

    url = url_base + "&page="+search_page_num
    
    # use a proxy handler as developing behind firewall
    proxyHandler = urllib2.ProxyHandler({"https": "http://localhost:3128"})
    opener = urllib2.build_opener(proxyHandler)
    #print "-----------url ="

    html = opener.open(url)
    #print url
    return html, howFarDownThePage
    




def any_results(html_parser) :
    return __count(html_parser) != 0 
    
    
def __create_imageId_array_from_html_page(website_search_results_parser, maxWanted, firstIdIndex) :
     """ Ids are in the javascript block following the div id=autoShowSimilars
     Note, will need re-writing if html changes """
     
     jsBlock_containing_list_of_image_ids = website_search_results_parser.find('input', id="autoShowSimilars").next.renderContents()
     
     # typical image_ids_text would be ['111', '2531', '13', '5343'], we find this, then break into an array of 4 numbers (list_of_image_ids)
     regex_for_image_ids_text = re.compile("\[\'\d{1,}\'.*\]")    #look for ['digit(s)'...]
     image_ids_text = regex_for_image_ids_text.findall(jsBlock_containing_list_of_image_ids)
     
     regex_for_list_of_image_ids = re.compile("(?<=\')\d+(?=\')")    # digits surrounded by ' '
     if image_ids_text[0]:
      list_of_image_ids = regex_for_list_of_image_ids.findall(image_ids_text[0])
      
      
     thumb_urls = []
     image_descriptions = []
   
     containing_divs = website_search_results_parser.findAll('div', 'pictureBox')  # class = 'pictureBox'
   
     #maxWanted = maxWanted if (maxWanted < len(containing_divs)) else len(containing_divs)
     maxWanted = len(list_of_image_ids)
     # get metadata for each image. Note, metadata div class depends on whether the image is available to the website
     for i in range(0, maxWanted) :
       metadata_div = containing_divs[i].find('img', 'mainThumbImage imageDraggable')
       if not metadata_div :    # couldn't find by normal class name, use alternative
           metadata_div = containing_divs[i].find('img', 'mainThumbImage ')   # class type if image not available
       # encode to UTF-8 because description might contain accents from other languages
       thumb_urls.append(BASE_THUMBNAIL_LOCATION_URL+metadata_div['src'].encode("UTF-8"))
       image_descriptions.append(metadata_div['title'].encode("UTF-8"))
    
      
     
     # only want maxWanted list_of_image_ids starting at firstIdIndex
     if (firstIdIndex > 0) :    # at start
         while firstIdIndex>0 :
	     firstIdIndex = firstIdIndex -1
             del list_of_image_ids[0]     # remove the first. Note this is not efficient, is there a better way?
             del thumb_urls[0]
             del image_descriptions[0]
     if (len(list_of_image_ids) > maxWanted) :     # at end
         while (len(list_of_image_ids) > maxWanted) :
             list_of_image_ids.pop()
             thumb_urls.pop()
             image_descriptions.pop()
             
     return (list_of_image_ids, thumb_urls, image_descriptions)
  




def __parse_html_for_image_details(website_search_results_parser, maxNumResults, firstIdIndex):
    list_of_image_ids, thumb_urls, image_descriptions = __create_imageId_array_from_html_page(website_search_results_parser, maxNumResults, firstIdIndex)
    
    #thumb_urls, image_descriptions = __create_arrays_for_thumbnailUrls_imageDescriptions(website_search_results_parser, maxNumResults)
    
    return (list_of_image_ids, thumb_urls, image_descriptions)
   

def __count(website_search_results_parser):
    containing_div = website_search_results_parser.find('div', 'breakdown')
    return int(re.findall("\d{1,}", containing_div.renderContents())[0])     # num results is the first number in this div
    
    
    
def count(keyword):
    # must be called 'count'"artist"
    
    # searchhtml  = __getHTMLPage_Containing_SearchResultX(term, {}, 0)[0]
    # website_search_results_parser = BeautifulSoup(searchhtml)
    # return __count(website_search_results_parser)
    return search(keyword, {}, 0, 0)[0].total

    
  
def __get_image_properties_from_imageSpecific_page(id) :
    """ Slower but more thorough method for finding metadata """
    
    page_url = BASE_IMAGE_PROPERTIES_URL + "?asset=" + id
    html = urllib2.build_opener(urllib2.ProxyHandler({"https": "http://localhost:3128"})).open(page_url)
    page_html_parser = BeautifulSoup(html)
    
    containing_div = page_html_parser.find('div', id="info", style=True)    # check for style, because there are two div with id info
    
    artist = containing_div.find('dd')    # first dd
    title = artist.findNextSibling('dd').findNextSibling('dd')
    date = title.findNextSibling('dd')    # note, not just numeric
    access = containing_div('dd')[-1]    # last dd in containing_div
    meta = {'artist': artist.renderContents(), 
            'title': title.renderContents(),
            'date': date.renderContents(),
            'access': access.renderContents()}
    
    return (title.renderContents(), meta) 
 
 
def __createImage(id, thumb, description) :
         
     image_url = BASE_IMAGE_LOCATION_URL + "=" + id
     image_identifier = {'id': id,
                         'image_url': image_url,
                         'thumb': thumb}
     
     image = ResultImage(image_url, thumb, description, json.dumps(image_identifier))
     return image
    

def getImage(json_image_identifier) :
    # return an Image
    
    image_identifier = json.loads(json_image_identifier)
    title, meta = __get_image_properties_from_imageSpecific_page(image_identifier['id'])
    return Image(image_identifier['image_url'], image_identifier['thumb'], title, meta, json_image_identifier)
    
#    dict_about_image = json.loads(json_dict_about_image)
#    
#    image_info = {'title': dict_about_image['title'],
#                  'artist': dict_about_image['artist'],
#                  }
#    
#    if dict_about_image['date'] :
#        image_info['date'] = dict_about_image['date']
#    if dict_about_image['access'] :
#        image_info['access'] = dict_about_image['access']
        
     
"""
WHY DOES THIS RETURN EMPTY PARAMS I DONT KNOW WHY
"""
def search(term, params, off, num_results_wanted) :
     #print term
     """ Get the actual results! Note, method must be called 'search'"""
     
     """print [ item.encode('ascii') for item in ast.literal_eval(term) ]
     """
     off = (int)(off)     # type of off varies by searcher implementation
     """
     print "In nga.py ln 236"
     print term
     print params
     """
     params, unsupported_params, url_base = build_parameters(term, params)
     no_query = True;
     #print params
     
     for p in params:
        if params[p][0]:
            no_query = False
     if no_query:
       print "Not searching NGA, no query given (nga.py ln 242)"
       return Result(0, off), empty_params
       
       
     # get the image details
     searchhtml, firstIdIndex = __getHTMLPage_Containing_SearchResult(url_base, off)
     website_search_results_parser = BeautifulSoup(searchhtml)
     
     if not any_results(website_search_results_parser) :
       return Result(0, off), empty_params
       
     list_of_image_ids, thumbnail_urls, image_descriptions = __parse_html_for_image_details(website_search_results_parser, num_results_wanted, firstIdIndex)
     
     
     # ensure the correct number of images found
     num_results_wanted = min(num_results_wanted, __count(website_search_results_parser))    # adjusted by how many there are to have
     
     
     #print "----------------------count  NGA------------"
     #print __count(website_search_results_parser)
     
     count = __count(website_search_results_parser)
     #print "___Count is ="
     #print count
     if off>count:
        return search(term,params,0,50)
     else:
        num_results_wanted = min(num_results_wanted, __count(website_search_results_parser)-off)
     """
     print"wanted"
     print num_results_wanted
     """
     if len(list_of_image_ids) < num_results_wanted:    # need more results and the next page has some
         tmp = 0
         while len(list_of_image_ids) < num_results_wanted and tmp<1:
             searchhtml, firstIdIndex = __getHTMLPage_Containing_SearchResult(url_base, off+len(list_of_image_ids))
             website_search_results_parser = BeautifulSoup(searchhtml)
             
             results = __parse_html_for_image_details(website_search_results_parser, num_results_wanted, firstIdIndex)
             if len(results[0])==0:
	       break
             if len(results[0])<25 :
	       tmp=1
             for i in range(0, len(results[0])) :
		# if not results[0][i] in list_of_image_ids:
		  list_of_image_ids.append(results[0][i]) 
		  thumbnail_urls.append(results[1][i])
		  image_descriptions.append(results[2][i])


                 
     if (len(list_of_image_ids) > num_results_wanted) :    # we've found too many, so remove some. Note, thumbs and image_descriptions self-regulate to never be more
         while (len(list_of_image_ids) > num_results_wanted) :
             list_of_image_ids.pop()
    
     
     # make Result that the rest of UnitedSearch can deal with
     resulting_images = Result(__count(website_search_results_parser), off+num_results_wanted)
     for i in range(len(list_of_image_ids)) :
         resulting_images.addImage(__createImage(list_of_image_ids[i], thumbnail_urls[i], image_descriptions[i]))
     """
     print "NGA params:"
     print params
     print empty_params
     """
     params = merge_dictionaries(empty_params, params, parameters.parammap.keys())[0]
     """
     print "NGA params:"
     print params
     """
     
     return resulting_images, params
     
"""
PARAMMAP
"""     
parameters = MapParameter({ 
    "all words": OptionalParameter(ScalarParameter(str)), 
    "exact phrase":
      OptionalParameter(ScalarParameter(str)), 
    "exclude words": OptionalParameter(ScalarParameter(str)),
    "artist": OptionalParameter(ScalarParameter(str)),
    "title": OptionalParameter(ScalarParameter(str)),
    "accession number": OptionalParameter(ScalarParameter(str)),
    "classification": OptionalParameter(ScalarParameter(str)),
    "school": OptionalParameter(ScalarParameter(str)),
    "medium": OptionalParameter(ScalarParameter(str)),
    "start date": OptionalParameter(ScalarParameter(str)),
    "end date": OptionalParameter(ScalarParameter(str)),
    "access": OptionalParameter(ScalarParameter(str))
    })
    
empty_params = {"all words": [],
    "exact phrase": [],
    "exclude words": [],
    "artist": [],
    "title": [],
    "accession number": [],
    "classification": [],
    "school": [],
    "medium": [],
    "start date": [],
    "end date": [],
    "access": []
    }
