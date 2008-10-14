import unittest
from ..data.models import Group, LABEL_MAX_LENGTH

class UniqueSlugTestCase(unittest.TestCase):
    
    def testUniqueSlugs(self):
        for i in range(100):
            Group.objects.create(title='T' * LABEL_MAX_LENGTH)
            
