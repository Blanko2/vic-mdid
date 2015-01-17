"""
Searcher for the National Gallery of Art website - also uses HTML parsing
  
Because NGA also uses HTML parsing it is likely to break in the future 
    the setup for NGA is a lot simpler than gallica and thus will be 
    easier to deal with.
Notes:
    NGA does not currently support the 'or' operator and it has     
        sepparate keywords for the '-' and '+' ops - 
        '-' is 'exclude words' and '+' is exact phrase
"""
from BeautifulSoup import BeautifulSoup      # html parser
from rooibos.unitedsearch import *       # other website search parts
from rooibos.unitedsearch.common import merge_dictionaries, proxy_opener, break_query_string, add_to_dict, getValue , list_to_str
from rooibos.unitedsearch.external.translator.query_language import Query_Language
from rooibos.unitedsearch.external.translator.nga_dict import query_dict
from rooibos.unitedsearch.external.translator.query_mod import query_mods
import json                                 # tool for encoding and decoding complex structures to/from string
import re                                   # regular expressions
import urllib2                               # fetch html

BASE_SIMPLE_SEARCH_URL = "https://images.nga.gov/?service=search&action=do_quick_search"
BASE_ADVANCED_SEARCH_URL = "https://images.nga.gov/en/search/show_advanced_search_page/?service=search&action=do_advanced_search&language=en&form_name=default"
BASE_IMAGE_PROPERTIES_URL = "https://images.nga.gov/en/asset/show_zoom_window_popup.html"
BASE_IMAGE_LOCATION_URL = "https://images.nga.gov/?service=asset&action=show_preview&asset"
BASE_THUMBNAIL_LOCATION_URL = "https://images.nga.gov/"
LOGO_URL = ""
HOMEPAGE_URL = "https://images.nga.gov"
# These variable names are fixed by the software requirements
name = "National Gallery of Art"    # database name that user will recognise
identifier = "nga"            # searcher identifier 
LOGO_URL = "http://www.nga.gov/images/eagle.gif"

def build_parameters(query, params):
    """ builds parameters dictionary to search by"""
    if not params:
        translator = Query_Language(identifier)
        params = translator.searcher_translator(query)
    all_words = getValue(params, 'all words')
    exact_phrase = list_to_str(getValue(params, 'exact phrase'))
    exclude = getValue(params, 'exclude words')
    not_in = getValue(params,'-')
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
    url_base = BASE_ADVANCED_SEARCH_URL + "&all_words="+list_to_str(all_words) + "&exact_phrase="+list_to_str(exact_phrase)+ "&exclude_words="+list_to_str(exclude)
    url_base += "&artist_last_name="+artist+"&keywords_in_title="+keywords + "&accession_num="+accession_number
    url_base += "&school="+list_to_str(school) + "&classification="+list_to_str(classification) + "&medium=" + list_to_str(medium) + "&year="+list_to_str(year1) + "&year2="+list_to_str(year2)
    url_base += "&open_access="+list_to_str(access)
    # replace all whitespace from the parameters
    url_base = re.sub(" ", "+", url_base)
    return params,  url_base

def any_results(html_parser) :
    """for checking if any results have been received"""
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
    return (list_of_image_ids, thumb_urls, image_descriptions)

def __count(website_search_results_parser):
    containing_div = website_search_results_parser.find('div', 'breakdown')
    return int(re.findall("\d{1,}", containing_div.renderContents())[0])     # num results is the first number in this div

def count(keyword):
    return search(keyword, {}, 0, 0)[0].total

def getImage(json_image_identifier) :
    # return an Image
    image_identifier = json.loads(json_image_identifier)
    title, meta = __get_image_properties_from_imageSpecific_page(image_identifier['id'])
    return RecordImage(image_identifier['image_url'], image_identifier['thumb'], title, meta, json_image_identifier)

def search(query, params, off, num_results_wanted) :
    try:
        """ 
        Gets search results - method must be called `search`
        query -- search query
        params -- parameters received from sidebar - if not sidebar they are empty
        off -- offset - number of images to offset the result by
        num_results_wanted -- images per page
        """
        if not query and params == {}:
            return Result(0, off), get_empty_params()
        arg = get_empty_params()
        off = (int)(off)    
        params,  url_base = build_parameters(query, params)
        no_query = True;
        if "query_string" in params:
            arg["query_string"] = fix_query_string(params["query_string"])
            del params["query_string"]
        else:
            query_string = ""
            if "all words" in params:
                query_string = params["all words"]
            for key in params:
                if not key == "all words":
                    if not query_string == "":
                        query_string += ","
                    value = list_to_str(params[key])
                    
                    query_string += query_dict[key] + "=" + value
            arg["query_string"] = fix_query_string(query_string)
            
        
        for key in params:
            value = params[key]
            if isinstance(value,list):
                value = list_to_str(value)
            
            no_query=False
            arg.update({key:value})
        if no_query:
            return Result(0, off), arg
        # get the image details
        searchhtml, firstIdIndex = __getHTMLPage_Containing_SearchResult(url_base, off)
        website_search_results_parser = BeautifulSoup(searchhtml)
        if not any_results(website_search_results_parser) :
            return Result(0, off), arg
        list_of_image_ids, thumbnail_urls, image_descriptions = __parse_html_for_image_details(website_search_results_parser, num_results_wanted, firstIdIndex)
        # ensure the correct number of images found
        num_results_wanted = min(num_results_wanted, __count(website_search_results_parser))    # adjusted by how many there are to have
        count = __count(website_search_results_parser)
        if off>count:
            return search(query,params,0,50)
        else:
            num_results_wanted = min(num_results_wanted, __count(website_search_results_parser)-off)
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
        if is_simple_search(arg):
            arg.update({"simple_keywords":str(arg["all words"])})
            arg.update({"all words":[]})
        return resulting_images, arg
    except:
        return Result(0, off), get_empty_params()
"""
================
TOOLS
===============
"""

def __parse_html_for_image_details(website_search_results_parser, maxNumResults, firstIdIndex):
    list_of_image_ids, thumb_urls, image_descriptions = __create_imageId_array_from_html_page(website_search_results_parser, maxNumResults, firstIdIndex)
    return (list_of_image_ids, thumb_urls, image_descriptions)

def __createImage(id, thumb, description) :
    image_url = BASE_IMAGE_LOCATION_URL + "=" + id
    image_identifier = {'id': id,
                        'image_url': image_url,
                        'thumb': thumb}
    image = ResultImage(image_url, thumb, description, json.dumps(image_identifier))
    return image

def __get_image_properties_from_imageSpecific_page(id) :
    """ Slower but more thorough method for finding metadata """
    page_url = BASE_IMAGE_PROPERTIES_URL + "?asset=" + id
    proxy_url = proxy_opener()
    html = proxy_url.open(page_url)
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

def __getHTMLPage_Containing_SearchResult(url_base, index_offset) :
    # set up fields for any type of search
    search_results_per_page = 25
    search_page_num = str(1 + (index_offset/search_results_per_page))   
    howFarDownThePage = index_offset % search_results_per_page
    url = url_base + "&page="+search_page_num
    # use a proxy handler as developing behind firewall
    proxy_url = proxy_opener()
    html = proxy_url.open(url)
    return html, howFarDownThePage

def fix_query_string(query_string):
    for mod in query_mods:
        if (mod+"=") in query_string:
            query_string = query_string.replace((mod+"="),mod)
    return query_string.replace("exclude words=","-").replace("exact phrase=","+")

def get_logo():
    return  LOGO_URL
def get_searcher_page():
    return HOMEPAGE_URL
"""
=============
PARAMMAP
=============
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
    
    
def get_empty_params():
    return {"all words": [],
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

def is_simple_search(arg):
    for key in arg:
        if not key == "all words":
            if not arg[key]==[]:
                return False
    return True
