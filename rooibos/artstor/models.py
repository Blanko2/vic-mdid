import urllib, urllib2, time
import cookielib
from os import makedirs
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates 
from rooibos.solr import SolrIndex
from rooibos.access.models import AccessControl
from rooibos.settings import ARTSTOR_GATEWAY

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        result.status = code
        return result                                

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        result.status = code              
        return result

class ArtstorSearch:

    def photoSearch(self, searchString="", page=1, per_page=50, summary=True):
        urlopen = urllib2.urlopen
        Request = urllib2.Request
        cj = cookielib.CookieJar()
        
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj), SmartRedirectHandler())
        urllib2.install_opener(opener)
        
        if summary: max_recs = 0
        else: max_recs = 1000
        
        params = {'query': searchString,
                  'version': '1.1',
                  'operation': 'searchRetrieve',
                  'startRecord': ((page-1) * per_page) + 1,
                  'maximumRecords': max_recs}
        
        txdata = urllib.urlencode(params)
        txheaders =  {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'}
        req = Request(ARTSTOR_GATEWAY, txdata, txheaders)
        handle = urlopen(req)

        results = ElementTree.ElementTree(file=handle)
        total = results.findtext('{http://www.loc.gov/zing/srw/}numberOfRecords')

        if searchString == "":
			return {"total": int(0), "page": int(0), "pages": int(0), "per_page": int(0), "photos": {}}

        raw_photos = results.findall('//{info:srw/schema/1/dc-v1.1}dc')
        photos = []                
        for photo in raw_photos:
            for ids in photo.findall('{http://purl.org/dc/elements/1.1/}identifier'):
                if ids.text.startswith('URL'):
                    url = ids.text[len('URL:'):]
                elif ids.text.startswith('THUMBNAIL'):
                    tn = ids.text[len('THUMBNAIL:'):]
                else:
                    id = ids.text
     
            title = photo.findtext('{http://purl.org/dc/elements/1.1/}title')
            photos.append({'id': id, 'title': title, 
                           'thumb': tn, 
                           'photo_page': url})

    return {"total": int(total), "page": int(page), "pages": int(pages), "per_page": int(per_page), "photos": photos}
