import unittest
from rooibos.data.models import Collection, Record, Field
from rooibos.storage.models import Storage
from models import AccessControl
from . import check_access, get_effective_permissions, filter_by_access, get_effective_permissions_and_restrictions
from django.contrib.auth.models import User, Group, AnonymousUser
from django.core.exceptions import PermissionDenied

class AccessTestCase(unittest.TestCase):

    def testGetEffectivePermissions(self):
        user = User.objects.create(username='test')
        collection = Collection.objects.create()
        self.assertEqual((None, None, None), get_effective_permissions(user, collection))
        
        usergroup1 = Group.objects.create(name='group1')
        usergroup2 = Group.objects.create(name='group2')        
        AccessControl.objects.create(content_object=collection, usergroup=usergroup1, read=True, write=False)
        AccessControl.objects.create(content_object=collection, usergroup=usergroup2, read=False, manage=True)
        self.assertEqual((None, None, None), get_effective_permissions(user, collection))

        user.groups.add(usergroup1)
        self.assertEqual((True, False, None), get_effective_permissions(user, collection))        

        user.groups.add(usergroup2)
        self.assertEqual((False, False, True), get_effective_permissions(user, collection))        

        AccessControl.objects.create(content_object=collection, user=user, read=True, manage=False)
        self.assertEqual((True, False, False), get_effective_permissions(user, collection))        


    def testCheckAccess(self):
        user = User.objects.create(username='test2')
        collection = Collection.objects.create()
        self.assertEqual(False, check_access(user, collection, read=True))

        AccessControl.objects.create(user=user, content_object=collection, read=True, write=True)
        
        self.assertEqual(True, check_access(user, collection, read=True))
        self.assertEqual(True, check_access(user, collection, read=True, write=True))
        self.assertEqual(False, check_access(user, collection, read=True, manage=True))

        try:
            check_access(user, collection, read=True, manage=True, fail_if_denied=True)
            self.assertEqual('result', 'this code should not run')
        except PermissionDenied:
            pass

    
    def testFilterByAccessUserOnly(self):
        user = User.objects.create(username='test3')
        group1 = Collection.objects.create()
        group2 = Collection.objects.create()
        group3 = Collection.objects.create()
        AccessControl.objects.create(user=user, content_object=group1, read=True, write=True)
        AccessControl.objects.create(user=user, content_object=group2, read=True)
        AccessControl.objects.create(user=user, content_object=group3, read=False)
        
        result = filter_by_access(user, Collection.objects.all())
        self.assertEqual(2, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(False, group3 in result)
        
        result = filter_by_access(user, Collection.objects.all(), read=True, write=True)
        self.assertEqual(1, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(False, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(user, Collection.objects.all(), manage=True)
        self.assertEqual(0, len(result))

    
    def testFilterByAccessUserGroup(self):
        
        user = User.objects.create(username='test5')
        group1 = Collection.objects.create()
        group2 = Collection.objects.create()
        group3 = Collection.objects.create()
        usergroup1 = Group.objects.create(name='group5a')
        usergroup2 = Group.objects.create(name='group5b')
        
        user.groups.add(usergroup1)
        user.groups.add(usergroup2)

        # collection 1 permissions
        AccessControl.objects.create(user=user, content_object=group1, read=True, write=True)
        
        # collection 2 permissions
        AccessControl.objects.create(user=user, content_object=group2, read=True)        
        AccessControl.objects.create(usergroup=usergroup1, content_object=group2, write=True)
        
        # collection 3 permissions
        AccessControl.objects.create(user=user, content_object=group3, read=True, manage=False)
        AccessControl.objects.create(usergroup=usergroup1, content_object=group3, read=True, write=True, manage=True)
        AccessControl.objects.create(usergroup=usergroup2, content_object=group3, write=False, manage=False)
        
        # checks
        result = filter_by_access(user, Collection.objects.all(), read=True)
        self.assertEqual(3, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(True, group3 in result)

        result = filter_by_access(user, Collection.objects.all(), read=True, write=True)
        self.assertEqual(2, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(True, group2 in result)
        self.assertEqual(False, group3 in result)

        result = filter_by_access(user, Collection.objects.all(), manage=True)
        self.assertEqual(0, len(result))


    def testAnonymousUserAccessControl(self):
        user = AnonymousUser()
        group1 = Collection.objects.create()
        group2 = Collection.objects.create()
        AccessControl.objects.create(content_object=group1, read=True)
        
        result = filter_by_access(user, Collection.objects.all(), read=True)
        self.assertEqual(1, len(result))
        self.assertEqual(True, group1 in result)
        self.assertEqual(False, group2 in result)
        
    def testAccessControl(self):
        user = User.objects.create(username='test4')
        usergroup = Group.objects.create(name='group4')
        collection = Collection.objects.create()
        storage = Storage.objects.create(name='test4')
        
        try:
            AccessControl.objects.create(user=user, usergroup=usergroup, content_object=collection)
            self.assertEqual('result', 'this code should not run')
        except ValueError:
            pass
    
    def testRestrictions(self):
        user = User.objects.create(username='test-restr')
        usergroup1 = Group.objects.create(name='group-restr-1')
        usergroup2 = Group.objects.create(name='group-restr-2')
        storage = Storage.objects.create(name='test-restr')
        user.groups.add(usergroup1)
        user.groups.add(usergroup2)
        
        AccessControl.objects.create(usergroup=usergroup1, content_object=storage, read=True,
                                     restrictions=dict(width=200, height=200))
        AccessControl.objects.create(usergroup=usergroup2, content_object=storage, read=True,
                                     restrictions=dict(width=300, height=300))

        (r, w, m, restrictions) = get_effective_permissions_and_restrictions(user, storage)        
        self.assertEqual(200, restrictions.get('width'))
        
        AccessControl.objects.create(user=user, content_object=storage, read=True,
                                     restrictions=dict(width=500, height=500))        

        (r, w, m, restrictions) = get_effective_permissions_and_restrictions(user, storage)        
        self.assertEqual(500, restrictions.get('width'))
