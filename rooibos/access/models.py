from django.db import models
from django.contrib.auth.models import User, Group as UserGroup
from rooibos.data.models import Group
from rooibos.storage.models import Storage

class AccessControl(models.Model):
    group = models.ForeignKey(Group, null=True)
    storage = models.ForeignKey(Storage, null=True)
    user = models.ForeignKey(User, null=True)
    usergroup = models.ForeignKey(UserGroup, null=True)
    read = models.BooleanField(null=True)
    write = models.BooleanField(null=True)
    manage = models.BooleanField(null=True)


