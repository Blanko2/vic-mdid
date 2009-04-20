import unittest
from models import Collection, CollectionItem, Record, Field
from datetime import datetime, timedelta
from django.contrib.auth.models import User

class FieldValueTestCase(unittest.TestCase):
    
    def setUp(self):
        self.collection = Collection.objects.create(title='Test Collection', name='test')
        self.titleField = Field.objects.create(label='Title', name='title')
        self.creatorField = Field.objects.create(label='Creator', name='creator')
        self.locationField = Field.objects.create(label='Location', name='location')
        self.user = User.objects.create(username='test')
        
    def tearDown(self):
        self.collection.delete()
        self.titleField.delete()
        self.creatorField.delete()
        self.locationField.delete()
        self.user.delete()
        
    def testFieldValueBasicContext(self):
        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=self.collection)
        
        t1 = record.fieldvalue_set.create(field=self.titleField, label='Caption', value='Photograph of Mona Lisa', type='T')
        t2 = record.fieldvalue_set.create(field=self.titleField, value='Photo Lisa', type='T')                
        c1 = record.fieldvalue_set.create(field=self.creatorField, label='Photographer', value='John Doe', type='T')
        c2 = record.fieldvalue_set.create(field=self.creatorField, value='John X. Doe', type='T', context=self.collection)
        l1 = record.fieldvalue_set.create(field=self.locationField, value='Harrisonburg', type='T', owner=self.user)
                
        self.assertEqual(True, datetime.now() - record.created < timedelta(0, 60))
        self.assertEqual(True, datetime.now() - record.modified < timedelta(0, 60))
        
        self.assertEqual("Caption", t1.resolved_label)
        self.assertEqual("Title", t2.resolved_label)
        
        self.assertEqual(3, len(record.get_fieldvalues()))
        self.assertEqual(4, len(record.get_fieldvalues(context=self.collection)))
        self.assertEqual(4, len(record.get_fieldvalues(owner=self.user)))
        self.assertEqual(5, len(record.get_fieldvalues(owner=self.user, context=self.collection)))
        
        
    def testFieldValueHide(self):
        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=self.collection)
        
        t1 = record.fieldvalue_set.create(field=self.titleField, value='Original', type='T')
        t2 = record.fieldvalue_set.create(field=self.titleField, override=t1, hidden=True, owner=self.user)
       
        self.assertEqual(1, len(record.get_fieldvalues(filter_overridden=True, filter_hidden=True)))
        self.assertEqual(0, len(record.get_fieldvalues(filter_overridden=True, filter_hidden=True, owner=self.user)))


class GroupTestCase(unittest.TestCase):

    def testSubGroups(self):
        group_a = Collection.objects.create(title='A', name='a')
        group_b = Collection.objects.create(title='B', name='b')
        group_b1 = Collection.objects.create(title='B1', name='b1')
        group_ab = Collection.objects.create(title='AB', name='ab')
        
        group_b.children.add(group_b1)
        group_b.save()
        
        group_ab.children.add(group_a, group_b)
        group_ab.save()
        
        self.assertEqual(0, len(group_b1.all_child_collections))
        self.assertEqual(1, len(group_b.all_child_collections))
        self.assertEqual(0, len(group_a.all_child_collections))
        self.assertEqual(3, len(group_ab.all_child_collections))
        
    def testCircularSubGroups(self):
        group_c = Collection.objects.create(title='C', name='c')
        group_d = Collection.objects.create(title='D', name='d')
        group_e = Collection.objects.create(title='E', name='e')
        
        group_c.children.add(group_d)
        group_c.save()
        
        group_d.children.add(group_c)
        group_d.save()
     
        self.assertEqual(1, len(group_c.all_child_collections))
        self.assertEqual(1, len(group_d.all_child_collections))
        
        group_e.children.add(group_e)
        group_e.save()
        
        self.assertEqual(0, len(group_e.all_child_collections))

    def testSubGroupRecords(self):
        group_f = Collection.objects.create(title='F', name='f')
        group_g = Collection.objects.create(title='G', name='g')
        group_h = Collection.objects.create(title='H', name='h')
        
        group_f.children.add(group_g)
        group_f.save()

        record = Record.objects.create()
        self.assertEqual(0, len(group_f.all_records))

        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_h)
        self.assertEqual(0, len(group_f.all_records))
        
        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_f)
        self.assertEqual(1, len(group_f.all_records))
        
        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_g)
        self.assertEqual(2, len(group_f.all_records))

        record = Record.objects.create()
        CollectionItem.objects.create(record=record, collection=group_f)
        CollectionItem.objects.create(record=record, collection=group_g)
        self.assertEqual(3, len(group_f.all_records))
        
    def testGetTitle(self):
        record1 = Record.objects.create()
        self.assertEqual(None, record1.title)
        
        dctitle = Field.objects.get(standard__prefix='dc', name='title')
        record1.fieldvalue_set.create(field=dctitle, value='The title')
        self.assertEqual('The title', record1.title)
        
        record2 = Record.objects.create()
        field = Field.objects.create(label='test', name='test')
        field.equivalent.add(dctitle)
        record2.fieldvalue_set.create(field=field, value='Another title')
        self.assertEqual('Another title', record2.title)
        