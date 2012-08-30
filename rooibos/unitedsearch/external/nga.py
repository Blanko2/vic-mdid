from BeautifulSoup import BeautifulSoup
import urllib2
import re
from rooibos.unitedsearch import *

SEARCH_BASE_URL = "https://images.nga.gov/?service=search&action=do_quick_search"
METADATA_BASE_URL = "https://images.nga.gov/en/asset/show_zoom_window_popup.html"
IMAGE_URL_BASE = "https://images.nga.gov/?service=asset&action=show_preview&asset"

name = "National Gallery of Art"
identifier = "nga"


def __getResultsHTML(query, paramenters,offset) :
     """ Ask the site itself to perform the search. Returns
     the page containing the offset'th image """
     
     page_num = offset/25    # 25 = num items per page on site
     startImNum = offset%25
     # simple search
     url = SEARCH_BASE_URL + "&q=" + query #+ "&page=" + page_num
     # html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
     proxy = urllib2.ProxyHandler({"https": "http://localhost:3128"})
     opener = urllib2.build_opener(proxy)
     html = opener.open(url)
     return BeautifulSoup(html), startImNum



def __findIds(soup, maxWanted, firstIdIndex) :
     """ Finds the javascript block following the div id=autoShowSimilars
     then gets an array holding numbers surrounded by ' '
     then breaks the array into the numbers and returns.
     Note, will need re-writing if html changes """
     
    
     # find the javascript containing the ids
     jsBlock = soup.find('input', id="autoShowSimilars").next
     
     # get ids from within the jsBlock
     listRegex = re.compile("\[\'\d{1,}\'.*\]")
     idList = listRegex.findall(jsBlock.renderContents())
     itemRegex = re.compile("(?<=\')\d+(?=\')")    # digits surrounded by ' '
     ids = itemRegex.findall(idList[0])
     
     # cut off any unwanted at start or end
     if (firstIdIndex > 0) :    # at start
         for numToRemove in (firstIdIndex, 0, -1) :
             ids.pop(0)     # remove the first. Note this is not efficient, is there a better way?
     if (len(ids) > maxWanted) :     # at end
         while (len(ids) > maxWanted) :
             ids.pop()
             
     return ids
  

  
def __findThumbUrls(soup, maxWanted) :
   """ get src for each image thumbnail """
   
   thumbs = []
   
   metaDataDivs = soup.findAll('div', 'pictureBox')  # class = 'pictureBox'
   
   maxIndex = maxWanted if (maxWanted < len(metaDataDivs)) else len(metaDataDivs)
   
   for i in range(0, maxIndex) :
       thumbs.append(divs[i].find('img', 'mainThumbImage imageDraggable')['src'])
   
   return thumbs



def __scrubHTML(soup, maxNumResults, firstIdIndex):
 ids = __findIds(soup, maxNumResults, firstIdIndex)
 thumbs = __findThumbUrls(soup, maxNumResults)
 return (ids, thumbs)
   

def __count(soup):
    containing_div = soup.find('div', 'breakdown')
    return re.findall("\d{1,}", containing_div.renderContents())[0]     # num results is the only number in the breakdown
    
    
    
def count(term):
    
    soup = __getResultsHTML(term, {}, 0)
    return __count(soup)
    

def __createImage(id, thumb) :
     
     metaUrl = METADATA_BASE_URL + "?asset=" + id
     html = urllib2.build_opener(urllib2.ProxyHandler({"https": "http://localhost:3128"})).open(metaUrl)
     metadataSoup = BeautifulSoup(html)
     
     info = metadataSoup.find('div', id="info", style=True)    # check for style, because there are two div with id info
     
     artist = info.find('dd')    # first dd
     title = artist.findNextSibling('dd').findNextSibling('dd')
     date = title.findNextSibling('dd')    # note, not just numeric
     access = info('dd')[-1]    # last dd in info
     meta = {'artist': artist, 
             'title': title,
             'date': date,
             'access': access}
     
     url = IMAGE_URL_BASE + "=" + id
     image = Image(url, thumb, title, meta, identifier+id)
    


def search(term, params, off, num_results_wanted) :
     """ Get the actual results! """
     
     # get image ids and thumbnail urls
     soup, firstIdIndex = __getResultsHTML(term, params, off)
     ids, thumbs = __scrubHTML(soup, num_results_wanted, firstIdIndex)
     
     # ensure the correct number of images found
     if (len(ids) < num_results_wanted) :    # need more results, check the next page
         while (len(ids) < num_results_wanted) :
             soup = __getResultsHTML(term, params, off+len(ids))
             results = __scrubHTML(soup, num_results_wanted, firstIdIndex+len(ids))
             ids.append(id in results[0])
             thumbs.append(id in results[1])
     if (len(ids) > num_results_wanted) :    # we've found too many, so remove some
         while (len(ids) > num_results_wanted) :
             ids.pop()
             thumbs.pop()
    
     
     # make Result that the rest of UnitedSearch can deal with
     result = Result(count(term), off+num_results_wanted)    # TODO should be actual count, not 2
     for i in range(len(ids)) :
         result.addImage(__createImage(ids[i], thumbs[i]))
       
     return result