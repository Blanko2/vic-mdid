import unittest
import tempfile
import os.path
from StringIO import StringIO
from django.test.client import Client
from django.core.files import File
from rooibos.data.models import *
from rooibos.storage.models import *
from localfs import LocalFileSystemStorageSystem

class LocalFileSystemStorageSystemTestCase(unittest.TestCase):
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.storage = Storage.objects.create(title='Test', name='test', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        
    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        self.record.delete()
        self.storage.delete()
    
    def test_retrieve_url(self):                        
        thumb = Media.objects.create(record=self.record, name='thumb', storage=self.storage)        
        self.assertEqual('/media/retrieve/monalisa/thumb/', thumb.get_absolute_url())
    
    def test_save_and_retrieve_file(self):
        media = Media.objects.create(record=self.record, name='image', storage=self.storage)
        content = StringIO('hello world')
        content.size = content.len
        media.save_file('test.txt', content)
        
        self.assertEqual('test.txt', media.url)

        content = media.load_file()
        self.assertEqual('hello world', content.read())
        
        