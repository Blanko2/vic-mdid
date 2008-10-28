import unittest
from ..data.models import Group, LABEL_MAX_LENGTH

class UniqueSlugTestCase(unittest.TestCase):
    
    def testLongUniqueSlugs(self):
        for i in range(100):
            Group.objects.create(title='T' * LABEL_MAX_LENGTH)
            
    def testUniqueSlugs(self):
        g = Group.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs', g.name)
        
        g = Group.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs-2', g.name)
        
        g = Group.objects.create(title='TestUniqueSlugs')
        self.assertEqual('testuniqueslugs-3', g.name)
        