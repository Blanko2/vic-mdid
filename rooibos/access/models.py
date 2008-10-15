from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group, Permission

class AccessControl(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    user_group = models.ForeignKey(Group)
    permission = models.ManyToManyField(Permission, through='PermissionDetail')
    
class PermissionDetail(models.Model):
    permission = models.ForeignKey(Permission)
    accesscontrol = models.ForeignKey(AccessControl)
    allow = models.BooleanField(default=True)
