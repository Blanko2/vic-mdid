from BeautifulSoup import BeautifulSoup      # html parser
import urllib2                               # fetch html
import re                                   # regular expressions
from rooibos.unitedsearch import *        # other website search parts
import json                                 # tool for encoding and decoding complex structures to/from string

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


def __getHTMLPage_Containing_SearchResult(query, parameters, first_wanted_result_index) :
     
     search_results_per_page = 25
     search_page_num = str(1 + (first_wanted_result_index/search_results_per_page))   
     howFarDownThePage = first_wanted_result_index % search_results_per_page
     
     # replace all whitespace in query with '+'
     query = re.sub("\W", "+", query)
     
     if parameters :
       # advanced search
       all_words = parameters.get('all_words', "")		# value if it exists, else ""
       exact_phrase = parameters.get('exact_phrase', "")
       exclude = parameters.get('exclude_words', "")
       artist = parameters.get('artist', "")
       keywords = parameters.get('keywords', "")
       accession_number = parameters.get('accession_number', "")
       school = parameters.get('school', "")
       classification = parameters.get('classification', "")
       medium = parameters.get('medium', "")
       year1 = parameters.get('start_date', "")
       year2 = parameters.get('end_date', "")
       access = parameters.get('access', "")
       
       url = BASE_ADVANCED_SEARCH_URL + "&all_words="+all_words + "&exact_phrase="+exact_phrase + "&exclude_words="+exclude
       url += "&artist_last_name="+artist + "&keywords_in_title="+keywords + "&accession_num="+accession_number
       url += "&school="+school + "&Classification="+classification + "&medium=" + medium + "&year="+year1 + "&year2="+year2
       url += "&open_access="+access + "&page="+search_page_num
       
       url = re.sub(" ", "+", url)
	 
     else :
       # simple search
	url = BASE_SIMPLE_SEARCH_URL + "&q=" + query + "&page=" + search_page_num


     # use a proxy handler in case user is behind firewall
     proxyHandler = urllib2.ProxyHandler({"https": "http://localhost:3128"})
     opener = urllib2.build_opener(proxyHandler)
     html = opener.open(url)
     
     return html, howFarDownThePage



def __create_imageId_array_from_html_page(website_search_results_parser, maxWanted, firstIdIndex) :
     """ Ids are in the javascript block following the div id=autoShowSimilars
     Note, will need re-writing if html changes """
     
     jsBlock_containing_list_of_image_ids = website_search_results_parser.find('input', id="autoShowSimilars").next.renderContents()
     
     # typical image_ids_text would be ['111', '2531', '13', '5343'], we find this, then break into an array of 4 numbers (list_of_image_ids)
     regex_for_image_ids_text = re.compile("\[\'\d{1,}\'.*\]")    #look for ['digit(s)'...]
     image_ids_text = regex_for_image_ids_text.findall(jsBlock_containing_list_of_image_ids)
     
     regex_for_list_of_image_ids = re.compile("(?<=\')\d+(?=\')")    # digits surrounded by ' '
     list_of_image_ids = regex_for_list_of_image_ids.findall(image_ids_text[0])
     
     # only want maxWanted list_of_image_ids starting at firstIdIndex
     if (firstIdIndex > 0) :    # at start
         for numToRemove in (firstIdIndex, 0, -1) :
             list_of_image_ids.pop(0)     # remove the first. Note this is not efficient, is there a better way?
     if (len(list_of_image_ids) > maxWanted) :     # at end
         while (len(list_of_image_ids) > maxWanted) :
             list_of_image_ids.pop()
             
     return list_of_image_ids
  

  
def __create_arrays_for_thumbnailUrls_imageDescriptions(website_search_results_parser, maxWanted) :
   
   thumb_urls = []
   image_descriptions = []
   
   containing_divs = website_search_results_parser.findAll('div', 'pictureBox')  # class = 'pictureBox'
   
   maxWanted = maxWanted if (maxWanted < len(containing_divs)) else len(containing_divs)
   
   # get metadata for each image. Note, metadata div class depends on whether the image is available to the website
   for i in range(0, maxWanted) :
       metadata_div = containing_divs[i].find('img', 'mainThumbImage imageDraggable')
       if not metadata_div :    # couldn't find by normal class name, use alternative
           metadata_div = containing_divs[i].find('img', 'mainThumbImage ')   # class type if image not available
       # encode to UTF-8 because description might contain accents from other languages
       thumb_urls.append(BASE_THUMBNAIL_LOCATION_URL+metadata_div['src'].encode("UTF-8"))
       image_descriptions.append(metadata_div['title'].encode("UTF-8"))
   
   return (thumb_urls, image_descriptions)


def __parse_html_for_image_details(website_search_results_parser, maxNumResults, firstIdIndex):
    list_of_image_ids = __create_imageId_array_from_html_page(website_search_results_parser, maxNumResults, firstIdIndex)
    
    thumb_urls, image_descriptions = __create_arrays_for_thumbnailUrls_imageDescriptions(website_search_results_parser, maxNumResults)
    
    return (list_of_image_ids, thumb_urls, image_descriptions)
   

def __count(website_search_results_parser):
    containing_div = website_search_results_parser.find('div', 'breakdown')
    return int(re.findall("\d{1,}", containing_div.renderContents())[0])     # num results is the first number in this div
    
    
    
def count(term):
    # must be called 'count'
    
    searchhtml  = __getHTMLPage_Containing_SearchResultX(term, {}, 0)[0]
    website_search_results_parser = BeautifulSoup(searchhtml)
    return __count(website_search_results_parser)
    

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
     
     
     # break description string into relevant parts
     # note, treat description string as title, even though it contains author and may contain artwork type and date
     # format of description is artist - title - date - type, with any unknown data missing
#     descr_parts = description.split("-")
#     
#     if len(descr_parts) == 1 :     # assume is title. May be solely artist, but that will do as title for user if untitled
#         title = descr_parts[0].strip()
#     elif len(descr_parts) >= 2 :
#         artist = descr_parts[0].strip()
#         title = descr_parts[1].strip()
#         
#         if descr_parts[2] :    # if contains number, assume is date. Else, assume type
#             if re.search("\d", descr_parts[2]) :
#                 date = descr_parts[2].strip()
#                 if descr_parts[3] :    # still more data => type
#                     type = descr_parts[3].strip()
#             else :
#                 type = descr_parts[3].strip()  # ignore any data after type, as don't know what it is
#
#     
#     image_identifier = {'title': title}
#     if artist :
#         image_identifier['artist'] = artist
#     if date :
#         image_identifier['date'] = date
#     if type :
#         image_identifier['type'] = type
#         
#     
#     
#
#                 
#     
#     if len(descr_parts) >= 2 :     # have both title and artist :)
#         artist = descr_parts[0].strip()
#         title = descr_parts[1].strip()
#         meta = {'artist': artist,
#                 'title': title}
#     else :     # only have partial info, need to go to image-specific page
#         title, meta = __get_image_properties_from_imageSpecific_page(id, thumb)
         
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
        
     

def search(term, params, off, num_results_wanted) :
     """ Get the actual results! Note, method must be called 'search'"""
     
     off = (int)(off)     # type of off varies by searcher implementation
     
     
     # get the image details
     searchhtml, firstIdIndex = __getHTMLPage_Containing_SearchResult(term, params, off)
     website_search_results_parser = BeautifulSoup(searchhtml)
     
     list_of_image_ids, thumbnail_urls, image_descriptions = __parse_html_for_image_details(website_search_results_parser, num_results_wanted, firstIdIndex)
     
     
     # ensure the correct number of images found
     num_results_wanted = min(num_results_wanted, __count(website_search_results_parser))    # adjusted by how many there are to have
     
     if len(list_of_image_ids) < num_results_wanted :    # need more results and the next page has some
         
         while len(list_of_image_ids) < num_results_wanted :
             searchhtml, firstIdIndex = __getHTMLPage_Containing_SearchResult(term, params, off+len(list_of_image_ids))
             website_search_results_parser = BeautifulSoup(searchhtml)
             
             results = __parse_html_for_image_details(website_search_results_parser, num_results_wanted, firstIdIndex)
             
             for i in range(0, len(results[0])) :
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
       
     return resulting_images 
     