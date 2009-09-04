import unittest
import urllib, urllib2, time, subprocess
from os import makedirs
from django.contrib.auth.models import User
from rooibos.data.models import Collection, CollectionItem, Record, Field, FieldSet
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
from rooibos.solr import SolrIndex
from rooibos.converters.models import PowerPointUploader

class PowerPointConverterTestCase(unittest.TestCase):

    def setup(self):
        dirname = self._get_path()+'/test'
        if not os.path.isdir("./" + dirname + "/"):
            os.mkdir("./" + dirname + "/")

    def tearDown(self):
        removeall(self._get_path()+'/test')

    def _get_path(self):
        return "C:/Program Files/OpenOffice.org 3/program/"

    def _save_file(self, targeturl, filename):
        try:
            req = urllib2.Request(targeturl)
            response = urllib2.urlopen(req)
            image = open('%s/%s' % (self.base, filename), 'wb')
            image.write(response.read())
            image.close()
        except Exception, deatil:
            print 'Error:', detail

    def test_convert_ppt(self):
        try:
            strCmd = '"' + '"' + self._get_path() + 'python.exe" "' + self._get_path() + 'DocumentConverter.py" "' + self._get_path() + 'test.ppt" "' + self._get_path() + 'test/test.html"' + '"'
            p = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in p.stdout.readlines():
                print line,
            retval = p.wait()
            print 'Return Value:', retval
            self.assertEqual(retval, 0)
        except Exception, detail:
            print 'Error:', detail

    def removeall(path):

        if not os.path.isdir(path):
            return

        files=os.listdir(path)

        for x in files:
            fullpath=os.path.join(path, x)
            if os.path.isfile(fullpath):
                f=os.remove
                rmgeneric(fullpath, f)
            elif os.path.isdir(fullpath):
                removeall(fullpath)
                f=os.rmdir
                rmgeneric(fullpath, f)
