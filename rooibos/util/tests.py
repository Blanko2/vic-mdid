import unittest
from ..data.models import Group

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
        