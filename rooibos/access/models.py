from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group

class AccessControl(models.Model):    
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, null=True)
    usergroup = models.ForeignKey(Group, null=True)
    read = models.BooleanField(null=True)
    write = models.BooleanField(null=True)
    manage = models.BooleanField(null=True)

    class Meta:
        unique_together = ('content_type', 'object_id', 'user', 'usergroup')
        
    def save(self, **kwargs):
        if (self.user and self.usergroup):
            raise ValueError("Mutually exclusive fields set")
        super(AccessControl, self).save(kwargs)

    def __unicode__(self):
        def f(flag, char):
            if flag == True: return char
            elif flag == False: return char.upper()
            else: return ' '
        return '%s %s%s%s %s' % (self.user or self.usergroup,
                                 f(self.read, 'r'), f(self.read, 'w'), f(self.manage, 'm'),
                                 self.content_object)
