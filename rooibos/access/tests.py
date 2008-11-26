import unittest
from rooibos.data.models import Group, Record, Field
from rooibos.storage.models import Storage
from models import AccessControl
from . import check_access, get_effective_permissions, filter_by_access
from django.contrib.auth.models import User, Group as UserGroup, AnonymousUser
from django.core.exceptions import PermissionDenied

class AccessTestCase(unittest.TestCase):

    def testGetEffectivePermissions(self):
        user = User.objects.create(username='test')
        group = Group.objects.create()
        self.assertEqual((None, None, None), get_effective_permissions(user, group))
        
        usergroup1 = UserGroup.objects.create(name='group1')
        usergroup2 = UserGroup.objects.create(name='group2')        
        AccessControl.objects.create(content_object=group, usergroup=usergroup1, read=True, write=False)
        AccessControl.objects.create(content_object=group, usergroup=usergroup2, read=False, manage=True)
        self.assertEqual((None, None, None), get_effective_permissions(user, group))

        user.groups.add(usergroup1)
        self.assertEqual((True, False, None), get_effective_permissions(user, group))        

        user.groups.add(usergroup2)
        self.assertEqual((False, False, True), get_effective_permissions(user, group))        

        AccessControl.objects.create(content_object=group, user=user, read=True, manage=False)
        self.assertEqual((True, False, False), get_effective_permissions(user, group))        


    def testCheckAccess(self):
        user = User.objects.create(username='test2')
        group = Group.objects.create()
        self.assertEqual(False, check_access(user, group, read=True))

        AccessControl.objects.create(user=user, content_object=group, read=True, write=True)
        
        self.assertEqual(True, check_access(user, group, read=True))
        self.assertEqual(True, check_access(user, group, read=True, write=True))
        self.assertEqual(False, check_access(user, group, read=True, manage=True))

        try:
            check_access(user, group, read=True, manage=True, fail_if_denied=True)
            self.assertEqual('result', 'this code should not run')
        except PermissionDenied:
            pass

    
    def testFilterByAccessUserOnly(self):
        user = User.objects.create(username='test3')
        group1 = Group.objects.create()
        group2 = Group.objects.create()
        group3 = Group.objects.create()
        AccessControl.objects.create(user=user, content_object=group1, read=True, write=True)
        AccessControl.objects.create(user=user, content_object=group2, read=True)
        AccessControl.objects.create(user=user, content_object=group3, read=False)
        
        result = filter_by_access(user, Group.objects.all())
        self.assertEqual(2, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(False, group3 in result)
        
        result = filter_by_access(user, Group.objects.all(), read=True, write=True)
        self.assertEqual(1, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(False, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(user, Group.objects.all(), manage=True)
        self.assertEqual(0, len(result))

    
    def testFilterByAccessUserGroup(self):
        
        user = User.objects.create(username='test5')
        group1 = Group.objects.create()
        group2 = Group.objects.create()
        group3 = Group.objects.create()
        usergroup1 = UserGroup.objects.create(name='group5a')
        usergroup2 = UserGroup.objects.create(name='group5b')
        
        user.groups.add(usergroup1)
        user.groups.add(usergroup2)

        # group 1 permissions
        AccessControl.objects.create(user=user, content_object=group1, read=True, write=True)
        
        # group 2 permissions
        AccessControl.objects.create(user=user, content_object=group2, read=True)        
        AccessControl.objects.create(usergroup=usergroup1, content_object=group2, write=True)
        
        # group 3 permissions
        AccessControl.objects.create(user=user, content_object=group3, read=True, manage=False)
        AccessControl.objects.create(usergroup=usergroup1, content_object=group3, read=True, write=True, manage=True)
        AccessControl.objects.create(usergroup=usergroup2, content_object=group3, write=False, manage=False)
        
        # checks
        result = filter_by_access(user, Group.objects.all(), read=True)
        self.assertEqual(3, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(True, group3 in result)

        result = filter_by_access(user, Group.objects.all(), read=True, write=True)
        self.assertEqual(2, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(user, Group.objects.all(), manage=True)
        self.assertEqual(0, len(result))


    def testAnonymousUserAccessControl(self):
        user = AnonymousUser()
        group1 = Group.objects.create()
        group2 = Group.objects.create()
        AccessControl.objects.create(content_object=group1, read=True)
        
        result = filter_by_access(user, Group.objects.all(), read=True)
        self.assertEqual(1, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(False, group2 in result)
        
    def testAccessControl(self):
        user = User.objects.create(username='test4')
        usergroup = UserGroup.objects.create(name='group4')
        group = Group.objects.create()
        storage = Storage.objects.create(name='test4')
        
        try:
            AccessControl.objects.create(user=user, usergroup=usergroup, content_object=group)
            self.assertEqual('result', 'this code should not run')
        except ValueError:
            pass
        