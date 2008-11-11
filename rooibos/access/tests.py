import unittest
from rooibos.data.models import Group, Record, Field
from models import AccessControl
from views import check_access, get_effective_permissions
from django.contrib.auth.models import User, Group as UserGroup

class AccessTestCase(unittest.TestCase):

    def testGetEffectivePermissions(self):
        user = User.objects.create(username='test')
        group = Group.objects.create()
        self.assertEqual((None, None, None), get_effective_permissions(user, group))
        
        usergroup1 = UserGroup.objects.create(name='group1')
        usergroup2 = UserGroup.objects.create(name='group2')        
        AccessControl.objects.create(group=group, usergroup=usergroup1, read=True, write=False)
        AccessControl.objects.create(group=group, usergroup=usergroup2, read=False, manage=True)
        self.assertEqual((None, None, None), get_effective_permissions(user, group))

        user.groups.add(usergroup1)
        self.assertEqual((True, False, None), get_effective_permissions(user, group))        

        user.groups.add(usergroup2)
        self.assertEqual((False, False, True), get_effective_permissions(user, group))        

        AccessControl.objects.create(group=group, user=user, read=True, manage=False)
        self.assertEqual((True, False, False), get_effective_permissions(user, group))        


    def testCheckAccess(self):
        user = User.objects.create(username='test2')
        group = Group.objects.create()
        self.assertEqual(False, check_access(user, group, read=True))

        AccessControl.objects.create(user=user, group=group, read=True, write=True)
        
        self.assertEqual(True, check_access(user, group, read=True))
        self.assertEqual(True, check_access(user, group, read=True, write=True))
        self.assertEqual(False, check_access(user, group, read=True, manage=True))
