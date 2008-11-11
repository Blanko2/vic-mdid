import unittest
from rooibos.data.models import Group, Record
from rooibos.storage.models import Media

class UniqueSlugTestCase(unittest.TestCase):
    
    def testLongUniqueSlugs(self):
        for i in range(100):
            Group.objects.create(title='T' * 50)
        for i in range(10):
            Group.objects.create(title='T' * 100)
        
            
    def testUniqueSlugs(self):
        g = Group.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs', g.name)
        
        g = Group.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs-2', g.name)
        
        g = Group.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs-3', g.name)
        
        
    def testUniqueWithSomethingSlugs(self):
        r1 = Record.objects.create()
        r2 = Record.objects.create()
        
        m1 = Media.objects.create(record=r1, name='thumb', url='m1')
        m2 = Media.objects.create(record=r2, name='thumb', url='m2')
        
        self.assertEqual('thumb', m1.name)
        self.assertEqual('thumb', m2.name)
        
        m2b = Media.objects.create(record=r2, name='thumb', url='m2b')
        
        self.assertEqual('thumb-2', m2b.name)