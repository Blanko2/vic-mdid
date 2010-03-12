import urllib2
from urllib import urlencode
from rooibos.util.BeautifulSoup import BeautifulSoup
from rooibos.data.models import *
from rooibos.storage.models import *
import mimetypes
from datetime import datetime, timedelta
import re

class NasaImageExchange():
    
    SERVER = "http://nix.nasa.gov/"
    
    def _get_form_defaults(self, form):
        data = {}
        for i in form.findAll('input', attrs={'name': True, 'type': lambda t: t != 'reset'}):
            data[i['name']] = i.get('value') or ''
        for i in form.findAll('select', attrs={'name': True}):
            data[i['name']] = i.find('option', selected=True).get('value') or ''
        return data
    
    _fix_record_url_re = re.compile(r';jsessionid=\w+')
    
    def _parse_result_page(self, soup):
        tags = [tag.parent.parent.parent for tag in soup.findAll(text='+ More Details')]
        return [
            {'full-url': tag.a['href'],
             'thumb-url': tag.a.img['src'],
             'date': tag.span.contents[0].strip(),
             'title': tag.span.contents[2].strip(),
             'record-url': self._fix_record_url_re.sub('', tag.find(text='+ More Details').parent['href'])}
            for tag in tags
        ]
    
    def search(self, keyword):
        soup = BeautifulSoup(urllib2.urlopen(self.SERVER))
        data = self._get_form_defaults(soup.form)
        data['qa'] = keyword
        soup = BeautifulSoup(urllib2.urlopen(soup.form['action'], urlencode(data)))        
        if soup.find(text="No matches found."):
            return None    
        result = self._parse_result_page(soup)
        # get additional result pages
        additional = soup.find(text='red')
        if additional:
            for page in [tag['href'] for tag in additional.parent.parent.findAll('a')]:
                result += self._parse_result_page(BeautifulSoup(urllib2.urlopen(page)))
        return self._create_records(result)

    def _mimetype(self, url):
        return mimetypes.guess_type(url, False)[0] or 'application/binary'

    def _create_records(self, result):
        try:
            storage = Storage.objects.get(name='nasaimageexchange')
        except Storage.DoesNotExist:
            storage = Storage.objects.create(title='NASA Image Exchange', name='nasaimageexchange', system='online')
        d = dict((r['record-url'],r) for r in result)
        records = list(Record.objects.filter(manager='nasaimageexchange', source__in=d.keys()))
        # find records that already exist
        for record in records:
            del(d[record.source])
            # TODO: update record title, date, urls
        # create missing records
        # TODO: add record to a NIX collection
        for r in d.values():
            record = Record.objects.create(name=r['title'],
                                           manager='nasaimageexchange',
                                           source=r['record-url'],
                                           next_update=datetime.now()+timedelta(28))
            records.append(record)
            record.media_set.create(name='thumb',
                                    url=r['thumb-url'],
                                    storage=storage,
                                    mimetype=self._mimetype(r['thumb-url']))
            record.media_set.create(name='full',
                                    url=r['full-url'],
                                    storage=storage,
                                    mimetype=self._mimetype(r['full-url']))
        return records
