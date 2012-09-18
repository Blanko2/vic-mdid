import re                                       # regular expressions
from BeautifulSoup import BeautifulSoup         # html parser
from unitedsearch import *                      # other search tools
import urllib2                                  # html fetcher
import json                                     # serialiser for data structures

# these field names are set by software requirement
name = "Gallica"        # database name the user will recognise
identifier = "gallica"  # identifier for view, urls


BASE_SIMPLE_SEARCH_URL = "http://gallica.bnf.fr/Search?ArianeWireIndex=index&f_typedoc=images" # append &q=query&pageNumber=number&lan
BASE_URL = "http://gallica.bnf.fr"


def __get_search_resultsHtml(term, params, first_index_wanted, items_per_page) :
    
    # calculate page number and items
    page_num = str(1 + (first_index_wanted/items_per_page))
         
    # build html to run through proxy
    url = BASE_SIMPLE_SEARCH_URL + "&q=" + term + "&pageNumber=" + page_num + "&lang=EN&tri=&n=" + str(items_per_page)
    html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
    return html

    

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
      # replace special char values with the actual characters, then strip off the resize part at the start
      thumb = regex_result.group('url').replace("%3A", ":").replace("%2F", "/").split("url=",1)[1] + regex_result.group('extension')
      # url has set width and height, we set to 2000x2000 here to allow scaling
      url = re.sub("WID\d*?(?=/)", "WID200", re.sub("HEI\d*?(?=\.)", "HEI200", thumb))
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
    
    return (int)(re.findall("\d{1,}", div.renderContents())[0])


def __scrub_html_for_property(property_name, html) :
    
    print "looking for " + property_name
    for para in html.findAll('p') :
        print para
        if para.strong and para.strong.renderContents().startswith(property_name) :
            print "found right para"
            contents = re.findall("(?<=\</strong\>).*", para.renderContents())
            if contents :
	      print "contents = " + contents[0]
	      return contents[0]
            
    
    return "None"
    

def getImage(json_image_identifier) :
    
    image_identifier = json.loads(json_image_identifier)
    descriptive_parser = BeautifulSoup(image_identifier['descriptive_html'])
    
    print "in getImage"
    meta = {'title': image_identifier['title'],
            'author': __scrub_html_for_property("Author", descriptive_parser),
            #'date': __scrub_html_for_property("Date", descriptive_parser),
            #'access': __scrub_html_for_property("Copyright", descriptive_parser)
            }
    
    print "made meta"
    print "url: " + image_identifier['url']
    print "thumb: " + image_identifier['thumb']
    
    return Image(
                 image_identifier['url'],
                 image_identifier['thumb'],
                 image_identifier['title'],
                 meta,
                 json_image_identifier)
    
    
def count(term) :
    return __count(__get_search_resultsHtml(term, {}, 0))
    

def search(term, params, off, num_wanted) :
    
    print "entered search"
    off = (int)(off)
    
    images = []
    search_results_parser = BeautifulSoup(__get_search_resultsHtml(term, params, off, __items_per_page(num_wanted)))
    num_results = __count(search_results_parser)
    num_wanted = min(num_wanted, num_results)    # how many were asked for mitigated by how many actually exist
    first_round = True      # optimisation to say we don't need to replace the first search_results_parser
    
    print "got first soup, about to start parsing"
    
    
    while len(images) < num_wanted :
        
        
        
        if not first_round :
            search_results_parser = BeautifulSoup(__get_search_resultsHtml(term, params, off+len(images), __items_per_page(num_wanted)))
        else :
            first_round = False
            
            
        # find start points for image data
        image_id_divs = search_results_parser.findAll('div', 'resultat_id')
        print "got image id divs"
         
        # discard any excess
        if len(image_id_divs) > num_wanted :
            while len(image_id_divs) > num_wanted :
                image_id_divs.pop()
                
        # build images
        print "about to make " + str(len(image_id_divs)) + "images"
        for div in image_id_divs :
            print "div id " + str(div.renderContents())
            images.append(__create_image(search_results_parser, div))
            print "made image - images len : " + str(len(images))
    
    
    print "about to build result"    
    # wrap in Result object and return
    result = Result(num_results, off+len(images))
    for image in images :
        print "about to add image"
        result.addImage(image)
        print "added image"
    return result