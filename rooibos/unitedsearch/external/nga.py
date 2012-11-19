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
  
  
def break_query_string_into_parameters(query) :
  print "NGA breaking query"
  keywords = ""
  para_map = {}
      
  # get any type=value arguements out of term
  type_value_pair_pattern = re.compile("[^,]+")		# break into tokens around commas
  tokens = re.findall(type_value_pair_pattern, query)
  second_pattern = re.compile("((?P<type>[^\"=]*)=)?(?P<value>.*)")	# break each token into type and value, separated by =
									# if no equals, treat whole token as the value
  # for each type-value pair, put into para_map
  # for each pair with only a value, add to keywords instead
  i=1
  for token in tokens :
    print "nga token: " + token
    m = second_pattern.match(token)
    if m.group('type') :
      k = ((str)(m.group('type').strip()))	# key
      v = (str(m.group('value').strip()))	# value
      if k=='search' : 
	para_map[0] = {k:v}
      else:
	para_map[i] = {k : v}
	i = i+1
      if k=='keywords' :
	keywords=v

  
  # write para_map, keywords into parameters
  print para_map
  
  
  return (keywords, para_map)

  
def __getHTMLPage_Containing_SearchResult(query, parameters, first_wanted_result_index) :
  
     # set up fields for any type of search
     print "NGA"
     print query
     search_results_per_page = 25
     search_page_num = str(1 + (first_wanted_result_index/search_results_per_page))   
     howFarDownThePage = first_wanted_result_index % search_results_per_page
     
     
     # if we have a query term, search by that. Else, search via the parameters
     if (query) :
      keywords, para_map = break_query_string_into_parameters(query)
      
      """keywords = ""
      search_type = "advance"

      para_map = {}
      
      # get any type=value arguements out of term
      first_pattern = re.compile("[^,]+")
      entries = re.findall(first_pattern, query)
      second_pattern = re.compile("((?P<type>[^\"=]*)=)?(?P<value>.*)")
      i=1
      for entry in entries :
	m = second_pattern.match(entry)
	if m.group('type') :
	  k = ((str)(m.group('type').strip()))
	  v = (str(m.group('value').strip()))
	  if k=='search' : 
	    para_map[0] = {k:v}
	  else:
	    para_map[i] = {k : v}
	    i = i+1
	  if k=='keywords' :
	    keywords=v
      print para_map"""


      def buildParams():
    
	p = {'End Date': [''], 'School': [''], 'Medium': [''], 'Exclude Words': [''], 'Classification': [''], 'Artist': [''], 'Exact Phrase': [''], 'Accession Number': [''], 'Access': [''], 'All words': [''], 'Keywords': [''], 'Start Date': ['']}

	print "P"
	print p
	
	for idx in para_map :
	  key = para_map[idx].keys()[0]
	  value = para_map[idx][key]
	  value = value.replace(' ','+')
	  print "KV"
	  print key
	  print value
	  if key=='keywords' :
	    p['Keywords'] = [value]
	  elif key=='creator_t' :
	    p['Artist'] = [value]
	    
	print p
	return p
      
      if para_map.has_key(0) :
	search_type = (para_map[0])["search"]
	print search_type
	if search_type == "simple" :
	  query = keywords
	  query = query.replace(' ','+')
	elif search_type == "advance" :
	  query = None
	  if len(parameters)==0 :
	    parameters=  buildParams()
      else :
	  search_type = "simple"
	  query = query.replace(" ","+")
     
     else :
       search_type = "advance"
     
     
     # replace all whitespace in query with '+'
     #query = re.sub("\W", "+", query)
     
     def __have_parameters(parameters) :
	return search_type == "advance"
	
	
     if __have_parameters(parameters) :
           
       # advanced search
       # TODO give user some hint of parameters form (eg, how to enter dates)
       
       # return either the value at 0 in the dictionary argument, or "" in none exists
       def getValue(a):
	 try:
	   r = str(a[0])
	   #r = a[0]
	 except IndexError:
	   r = ""
	 if isinstance(r, str): return r
	 return ""

       # get the parameter values to put into the url
       all_words = getValue(parameters['All words'])
       exact_phrase = getValue(parameters['Exact Phrase'])
       exclude = getValue(parameters['Exclude Words'])

       artist = getValue(parameters['Artist'])
       keywords = getValue(parameters['Keywords'])
       
       accession_number = getValue(parameters['Accession Number'])
       school = getValue(parameters['School'])
       classification = getValue(parameters['Classification'])
       medium = getValue(parameters['Medium'])
       year1 = getValue(parameters['Start Date'])
       year2 = getValue(parameters['End Date'])
       access = getValue(parameters['Access'])

       # add the actual query itself, if it exists
       """if query :
	 keywords += " " + query"""
    
       # build up the url
       url = BASE_ADVANCED_SEARCH_URL + "&all_words="+all_words + "&exact_phrase="+exact_phrase+ "&exclude_words="+exclude
       
       url += "&artist_last_name="+artist+"&keywords_in_title="+keywords + "&accession_num="+accession_number
       
       url += "&school="+school + "&Classification="+classification + "&medium=" + medium + "&year="+year1 + "&year2="+year2
       
       url += "&open_access="+access + "&page="+search_page_num
       
       # replace all whitespace from the parameters
       url = re.sub(" ", "+", url)

	 
     else :
       # simple search
	url = BASE_SIMPLE_SEARCH_URL + "&q=" + query + "&page=" + search_page_num

     print url
     # use a proxy handler as developing behind firewall
     proxyHandler = urllib2.ProxyHandler({"https": "http://localhost:3128"})
     opener = urllib2.build_opener(proxyHandler)
     html = opener.open(url)
     print url
     return html, howFarDownThePage


def any_results(html_parser) :
    have_no_results_tag = html_parser.find('h5')
    return not have_no_results_tag 
    
    
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
    # must be called 'count'"artist"
    
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
     
     """print [ item.encode('ascii') for item in ast.literal_eval(term) ]
     """
     off = (int)(off)     # type of off varies by searcher implementation
     
     
     # get the image details
     searchhtml, firstIdIndex = __getHTMLPage_Containing_SearchResult(term, params, off)
     website_search_results_parser = BeautifulSoup(searchhtml)
     
     if not any_results(website_search_results_parser) :
       return Result(0, off)
       
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
     
     
parameters = MapParameter({ 
    "All words": OptionalParameter(ScalarParameter(str)), 
    "Exact Phrase":
      OptionalParameter(ScalarParameter(str)), 
     "Exclude Words": OptionalParameter(ScalarParameter(str)),
    "Artist": OptionalParameter(ScalarParameter(str)),

  
    "Keywords": OptionalParameter(ScalarParameter(str)),
    "Accession Number": OptionalParameter(ScalarParameter(str)),
    "Classification": OptionalParameter(ScalarParameter(str)),
    "School": OptionalParameter(ScalarParameter(str)),
    "Medium": OptionalParameter(ScalarParameter(str)),
    "Start Date": OptionalParameter(ScalarParameter(str)),
    "End Date": OptionalParameter(ScalarParameter(str)),
    "Access": OptionalParameter(ScalarParameter(str))
 
    
    })