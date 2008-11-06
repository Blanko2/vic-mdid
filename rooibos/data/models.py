from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from datetime import datetime
from rooibos.util.util import unique_slug
import random

class Group(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    subgroups = models.ManyToManyField('self', symmetrical=False)
    records = models.ManyToManyField('Record')
    owner = models.ForeignKey(User, null=True)
    hidden = models.BooleanField(default=False)
    description = models.TextField(null=True)
    agreement = models.TextField(null=True)
    password = models.CharField(max_length=32, null=True)
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name')
        super(Group, self).save(kwargs)
        
    def __unicode__(self):
        return self.name

    def _resolve_subgroups(self, include_self=False):
        sub = list(self.subgroups.all())
        result = include_self and (self,) or ()
        while True:
            todo = ()
            for group in sub:
                if self != group:
                    result += (group,)
                for g in group.subgroups.all():
                    if g != self and not g in sub:
                        todo += (g,)
            if not todo:
                break
            sub = todo            
        return result
    all_subgroups = property(_resolve_subgroups)
    
    def _resolve_parent_groups(self, include_self=False):
        parents = list(self.group_set.all())
        result = include_self and (self,) or ()
        while True:
            todo = ()
            for group in parents:
                if self != group:
                    result += (group,)
                for g in group.group_set.all():
                    if g != self and not g in parents:
                        todo += (g,)
            if not todo:
                break
            sub = todo            
        return result
    all_parent_groups = property(_resolve_parent_groups)
        
    
    def _get_records(self):
        return Record.objects.filter(group__in=self._resolve_subgroups(include_self=True)).distinct()
    all_records = property(_get_records)

class Record(models.Model):
    created = models.DateTimeField(default=datetime.now())
    modified = models.DateTimeField(auto_now=True)
    name = models.SlugField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True)
    source = models.CharField(max_length=1000, null=True)
    manager = models.CharField(max_length=50, null=True)
    next_update = models.DateTimeField(null=True)
    owner = models.ForeignKey(User, null=True)
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(null=True)
    
    def __unicode__(self):
        return self.name or 'unnamed'
    
    def _generate_slug(self):        
        return self._preferred_name or "r-%s" % random.randint(1000000, 9999999)
    _generated_slug = property(_generate_slug)
    _preferred_name = None

    def save(self, **kwargs):
        if kwargs.get('force_insert'):
            self._preferred_name = self.name
            self.name = ''
        unique_slug(self, slug_source='_generated_slug', slug_field='name')
        super(Record, self).save(kwargs)
        
    def get_fieldvalues(self, owner=None, group=None, for_display=False):
        values = self.fieldvalue_set.filter(Q(group=group) | Q(group=None), Q(owner=owner) | Q(owner=None))
        if not for_display:
            return values
        remove = ()
        for v in values:
            if v.override:
                remove += (v.override.id,)
            if v.hidden:
                remove += (v.id,)
        return values.exclude(id__in=remove)
    
    def dump(self, owner=None, group=None):
        print("Created: %s" % self.created)
        print("Modified: %s" % self.modified)
        print("Name: %s" % self.name)
        for v in self.fieldvalue_set.all():
            v.dump(owner, group)

class Field(models.Model):
    label = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    owner = models.ForeignKey(User, null=True)

    def save(self, **kwargs):
        unique_slug(self, slug_source='label', slug_field='name')
        super(Field, self).save(kwargs)

    def __unicode__(self):
        return self.name
    
class FieldValue(models.Model):
    TYPE_CHOICES = (
        ('T', 'Text'),
        ('D', 'Date'),
        ('N', 'Numeric'),
    )
    record = models.ForeignKey(Record)
    field = models.ForeignKey(Field)
    owner = models.ForeignKey(User, null=True)
    label = models.CharField(max_length=100, null=True)
    override = models.ForeignKey('self', null=True)
    hidden = models.BooleanField(default=False)
    value = models.TextField()
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    language = models.CharField(max_length=5, null=True)
    group = models.ForeignKey(Group, null=True)
    order = models.IntegerField(null=True)
    
    def __unicode__(self):
        return "%s=%s" % (self.label, self.value[:20])
    
    def resolve_label(self):
        return self.label or self.field.label
    resolved_label = property(resolve_label)
    
    def dump(self, owner=None, group=None):
        print("%s: %s" % (self.resolved_label, self.value))
        