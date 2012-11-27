# Copyright (C) 2009 Mark A. Matienzo
#
# This file is part of the digitalnz Python module.
#
# digitalnz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# digitalnz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with digitalnz.  If not, see <http://www.gnu.org/licenses/>.

# request.py - request classes

from urllib import urlencode as uenc
import urllib2
from digitalnz.response import DigitalNZResponse


class DigitalNZAPI(object):
    """DigitalNZAPI: class to perform requests to the APIs
    
    Example usage:
    
    >>> import digitalnz
    >>> request = digitalnz.request.DigitalNZAPI(api_key=YOUR_API_KEY)
    >>> result = request.search(search_text="hacker")
    >>> print result.data.keys()
    [u'start', u'num_results_requested', u'api_call', u'results', u'result_count']
    >>> print result.data['result_count']
    17
    >>> print result.data['results'][0]
    {u'category': u'Manuscripts', u'description': u'Trooper Arthur Hacker.World War I, 1914-1918.Auckland Mounted Rifles.Gallipoli, Turkey', u'title': u'Trooper Arthur Hacker', u'metadata_url': u'http://api.digitalnz.org/records/v1/151818', u'display_url': u'http://muse.aucklandmuseum.com/databases/Cenotaph/6052.detail', u'source_url': u'http://api.digitalnz.org/records/v1/151818/source', u'thumbnail_url': u'', u'content_provider': u'Auckland War Memorial Museum Tamaki Paenga Hira', u'date': u'', u'syndication_date': u'2009-03-25T06:40:19.932Z', u'id': u'151818'}
    """

    def __init__(self, api_key=None, version=1, format='json', parsing=True):
        if api_key is None:
            raise RuntimeError, "Missing Digital NZ API key"
        else:
            self.api_key = api_key
        self.base_url = 'http://api.digitalnz.org'
        self.parsing = parsing
        self.version = version
        self.format = format


    def search(self, **kwargs):
        args = kwargs
        req_url = '%s/records/v%s.%s?api_key=%s&%s' % (\
            self.base_url,
            self.version,
            self.format,
            self.api_key,
            uenc(kwargs))
        print 'request L~60'
        print req_url
        #TODO: return this to how it was? 
        #rsp = urllib2.urlopen(req_url).read()
        rsp = self._proxy_handling(req_url).read() 
        return DigitalNZResponse(self, rsp)

    def custom_search(self, title=None, **kwargs):
        args = kwargs
        if title is None:
            raise
        req_url = '%s/custom_searches/v%s/%s.%s?api_key=%s&%s' % (\
            self.base_url,
            self.version,
            title,
            self.format,
            self.api_key,
            uenc(kwargs))
        rsp = urllib2.urlopen(req_url).read()
        return DigitalNZResponse(self, rsp)        


    def metadata(self, rec_num=None):
        if rec_num is None:
            raise
        req_url = '%s/records/v%s/%s.%s?api_key=%s' % (\
            self.base_url,
            self.version,
            rec_num,
            self.format,
            self.api_key)
        rsp = urllib2.urlopen(req_url).read()
        return DigitalNZResponse(self, rsp)


    def partners(self):
        req_url = '%s/content_partners/v%s.%s?api_key=%s' % (\
            self.base_url,
            self.version,
            self.format,
            self.api_key)
        rsp = urllib2.urlopen(req_url).read()
        return DigitalNZResponse(self, rsp)


    """
    custom code for proxy handling
    """
    def _proxy_handling(self,url):
        html = urllib2.build_opener(urllib2.ProxyHandler({"http": "http://localhost:3128"})).open(url)
        return html
    
