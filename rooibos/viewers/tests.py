from __future__ import with_statement
import unittest
from rooibos.data.models import Collection, CollectionItem, Record, Field, FieldValue
from rooibos.storage.models import Media, Storage
from rooibos.presentation.models import Presentation, PresentationItem
from presentations.powerpoint import PowerPointGenerator
import os
import tempfile

class PowerpointTestCase(unittest.TestCase):
        
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.storage = Storage.objects.create(title='PPTXTest', name='pptxtest', system='local', base=self.tempdir)
        
    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        self.storage.delete()
    
    def testSimplePowerpointFile(self):
        file = os.path.join(self.tempdir, 'test.pptx')
        collection = Collection.objects.create(title='Simple Collection', description='Simple collection')
        field = Field.objects.get(name='title', standard__prefix='dc')
        presentation = Presentation.objects.create(title='Simple Presentation', description='This is a PowerPoint presentation created from a template and populated with data.')
        for n in range(1, 11):
            record = Record.objects.create()
            FieldValue.objects.create(record=record, field=field, value='Record %s' % n)
            CollectionItem.objects.create(collection=collection, record=record)
            PresentationItem.objects.create(presentation=presentation, record=record, order=n)
            media = Media.objects.create(record=record, storage=self.storage, mimetype='image/jpeg')
            with open(os.path.join(os.path.dirname(__file__), 'presentations/powerpoint/test_data', '%02d.jpg' % n), 'rb') as f:
                media.save_file('%02d.jpg' % n, f)            
        
        g = PowerPointGenerator(presentation)
        
        self.assertTrue(g.generate(g.get_templates()[0], file))
        