from django.db import models
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from rooibos.contrib.ipaddr import IP


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


EVERYBODY_GROUP = 'E'
AUTHENTICATED_GROUP = 'A'
IP_BASED_GROUP = 'I'
ATTRIBUTE_BASED_GROUP = 'P'


class ExtendedGroupManager(models.Manager):
    
    def get_extra_groups(self, user):
        # retrieve membership in special groups such as everyone and authenticated users
        # membership for those types of groups is not stored explicitly
        q = Q(type=EVERYBODY_GROUP)
        if user.is_authenticated():
            q = q | Q(type=AUTHENTICATED_GROUP)
        return self.filter(q)
        
    def update_membership(self, user, info={}):
        for group in ExtendedGroup.objects.all():
            group.update_membership(user, info)
            

class ExtendedGroup(Group):
    TYPE_CHOICES = (
        ('A', 'Authenticated'),
        ('I', 'IP Address based'),
        ('P', 'Attribute based'),
        ('E', 'Everybody'),
    )
    
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    
    objects = ExtendedGroupManager()
    
    def update_membership(self, user, info={}):
        # to be called upon a user login        
        if self.type == IP_BASED_GROUP:
            # update membership of IP address based groups
            include = info.has_key('ip') and self._check_subnet(info['ip'])
        elif self.type == ATTRIBUTE_BASED_GROUP:
            # update membership of attribute based groups
            include = info.has_key('attr') and self._check_attributes(info['attr'])
        else:
            return

        if include:
            self.user_set.add(user)
        else:
            self.user_set.remove(user)
    
    def _check_subnet(self, address):
        ip = IP(address)
        for subnet in self.subnet_set.values_list('subnet', flat=True):
            if ip in IP(subnet):
                return True
        return False
    
    def _check_attributes(self, attributes):
        for attribute in Attribute.objects.filter(group=self):
            values = attributes.get(attribute.attribute, [])
            for value in attribute.attributevalue_set.all().values_list('value', flat=True):
                if (hasattr(values, '__iter__') and value in values) or value == values:
                    break
            else:
                return False
        return True

    def _full_type(self):
        return filter(lambda (a,f): a==self.type, self.TYPE_CHOICES)[0][1]

    def __unicode__(self):
        return '%s (%s)' % (self.name, self._full_type())
    
class Subnet(models.Model):
    group = models.ForeignKey(ExtendedGroup, limit_choices_to={'type': 'I'})
    subnet = models.CharField(max_length=80)
    
    def __unicode__(self):
        return '%s: %s' % (self.group.name, self.subnet)
    
    
class Attribute(models.Model):
    group = models.ForeignKey(ExtendedGroup, limit_choices_to={'type': 'P'})
    attribute = models.CharField(max_length=255)
    
    def __unicode__(self):
        return '%s: %s' % (self.group.name, self.attribute)
    
    
class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute)
    value = models.CharField(max_length=255)

