from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group as UserGroup, Permission
from ..data.models import Group

class AccessControl(models.Model):
    group = models.ForeignKey(Group)
    user = models.ForeignKey(User, null=True)
    usergroup = models.ForeignKey(UserGroup, null=True)
    read = models.BooleanField(null=True)
    write = models.BooleanField(null=True)
    manage = models.BooleanField(null=True)


def get_effective_permissions(user, group):
    aclist = AccessControl.objects.filter(Q(user=user) | Q(usergroup__in=user.groups.all()), group=group)    
    def reduce_by_filter(f):
        def combine(a, b):
            if a == False or (a == True and b == None):
                return a
            else:
                return b
        read = write = manage = None
        for ac in filter(f, aclist):
            read = combine(ac.read, read)
            write = combine(ac.write, write)
            manage = combine(ac.manage, manage)
        return (read, write, manage)
    
    (gr, gw, gm) = reduce_by_filter(lambda a: a.usergroup)
    (ur, uw, um) = reduce_by_filter(lambda a: a.user)
    
    return (ur or (ur == None and gr),
            uw or (uw == None and gw),
            um or (um == None and gm))
