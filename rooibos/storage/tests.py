import unittest
import tempfile
import os.path
from django.test.client import Client
from rooibos.data.models import *
from rooibos.storage.models import *
from localfs import LocalFileSystemStorageSystem

class LocalFileSystemStorageSystemTestCase(unittest.TestCase):
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        
    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
    
    def test_retrieve_url(self):
        storage = Storage.objects.create(title='Test', name='test', system='local', base=self.tempdir)        
        record = Record.objects.create(name='monalisa')
        thumb = Media.objects.create(record=record, name='thumb', storage=storage)
        
        self.assertEqual('/media/retrieve/monalisa/thumb/', thumb.get_absolute_url())
        
        c = Client()
        response = c.get(thumb.get_absolute_url())
        self.assertEqual(200, response.status_code)
        