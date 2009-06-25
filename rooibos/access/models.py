from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group

#class AccessControlManager(models.Manager):
    #def create(self, **kwargs):
    #    #print kwargs
    #    #if kwargs.has_key('restrictions'):
    #    #    kwargs['restrictions_repr'] = repr(kwargs['restrictions'])
    #    #    del kwargs['restrictions']
    #    #print kwargs
    #    super(AccessControlManager, self).create(**kwargs)


class AccessControl(models.Model):    
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, null=True, blank=True)
    usergroup = models.ForeignKey(Group, null=True, blank=True)
    read = models.NullBooleanField()
    write = models.NullBooleanField()
    manage = models.NullBooleanField()
    restrictions_repr = models.TextField(blank=True, default='')
#    objects = AccessControlManager()

    #def __init__(self, **kwargs):
    #    #if kwargs.has_key('restrictions'):
    #    #    kwargs['restrictions_repr'] = repr(kwargs['restrictions'])
    #    #    del kwargs['restrictions']
    #    super(AccessControl, self).__init__(kwargs)

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
            else: return '-'
        return '%s [%s%s%s] %s (%s)' % (self.user or self.usergroup or 'AnonymousUser',
                                 f(self.read, 'r'), f(self.write, 'w'), f(self.manage, 'm'),
                                 self.content_object, self.content_type)

    def restrictions_get(self):
        if self.restrictions_repr:
            return eval(self.restrictions_repr, {"__builtins__": None}, {})
        else:
            return None

    def restrictions_set(self, value):
        if value:
            self.restrictions_repr = repr(value)
        else:
            self.restrictions_repr = ''
        
    restrictions = property(restrictions_get, restrictions_set)
