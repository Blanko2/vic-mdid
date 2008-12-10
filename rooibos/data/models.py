from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.cache import cache
from datetime import datetime
from rooibos.util import unique_slug, cached_property, clear_cached_properties
import random

class Group(models.Model):
    
    TYPE_CHOICES = (
        ('collection', 'Collection'),
        ('presentation', 'Presentation'),
        ('folder', 'Folder'),
    )
    
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    subgroups = models.ManyToManyField('self', symmetrical=False)
    records = models.ManyToManyField('Record', through='GroupMembership')
    owner = models.ForeignKey(User, null=True)
    hidden = models.BooleanField(default=False)
    description = models.TextField(null=True)
    agreement = models.TextField(null=True)
    password = models.CharField(max_length=32, null=True)
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Group, self).save(kwargs)
        
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('data-group', kwargs={'groupname': self.name})
    
    @property
    def all_subgroups(self):
        sub = list(self.subgroups.all())
        result = ()
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
    
    @property
    def all_parent_groups(self):
        parents = list(self.group_set.all())
        result = ()
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
            
    @property
    def all_records(self):
        return Record.objects.filter(group__in=self.all_subgroups + (self,)).distinct()


class GroupMembership(models.Model):
    group = models.ForeignKey('Group')
    record = models.ForeignKey('Record')
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(null=True)


class Record(models.Model):
    created = models.DateTimeField(default=datetime.now())
    modified = models.DateTimeField(auto_now=True)
    name = models.SlugField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True)
    source = models.CharField(max_length=1024, null=True)
    manager = models.CharField(max_length=50, null=True)
    next_update = models.DateTimeField(null=True)
    owner = models.ForeignKey(User, null=True)
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('data-record', kwargs={'recordname': self.name})

    def save(self, **kwargs):
        unique_slug(self, slug_literal='r-%s' % random.randint(1000000, 9999999),
                    slug_field='name', check_current_slug=kwargs.get('force_insert'))
        self._clear_cached_items()
        super(Record, self).save(kwargs)
        
    def get_fieldvalues(self, owner=None, group=None,
                        filter_overridden=False, filter_hidden=False, filter_context=False):
        q_group = Q(group=group)
        if not filter_context:
            q_group = q_group | Q(group=None)
        
        q_owner = Q(owner=owner)
        if not filter_context:
            q_owner = q_owner | Q(owner=None)
        
        values = self.fieldvalue_set.filter(q_group, q_owner)
        remove = []
        for v in values:
            if filter_overridden and v.override_id:
                remove.append(v.override_id)
            if filter_hidden and v.hidden:
                remove.append(v.id)
        return values.exclude(id__in=remove)
    
    def dump(self, owner=None, group=None):
        print("Created: %s" % self.created)
        print("Modified: %s" % self.modified)
        print("Name: %s" % self.name)
        for v in self.fieldvalue_set.all():
            v.dump(owner, group)

    @property            
    def title(self):
        def query():
            return self.fieldvalue_set.filter(
                Q(field__standard__prefix='dc', field__name='title') |
                Q(field__equivalent__standard__prefix='dc', field__equivalent__name='title'))[0].value
        return cached_property(self, 'title', query)

    def _clear_cached_items(self):
        clear_cached_properties(self, 'title', 'thumbnail')
        


class MetadataStandard(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    prefix = models.CharField(max_length=16, unique=True)

    def __unicode__(self):
        return self.title

class Field(models.Model):
    label = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    standard = models.ForeignKey(MetadataStandard, null=True, blank=True)
    equivalent = models.ManyToManyField("self", null=True, blank=True)

    def save(self, **kwargs):
        unique_slug(self, slug_source='label', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Field, self).save(kwargs)

    def __unicode__(self):
        if self.standard:
            return "%s:%s" % (self.standard.prefix, self.name)
        else:
            return self.name
    
    class Meta:
        unique_together = ('name', 'standard')
        ordering = ['name']
        order_with_respect_to = 'standard'
    
    
class FieldValue(models.Model):
    TYPE_CHOICES = (
        ('T', 'Text'),
        ('D', 'Date'),
        ('N', 'Numeric'),
    )
    LANGUAGE_CHOICES = (
        ('en-us', 'English (United States)'),
    )
    
    record = models.ForeignKey(Record, editable=False)
    field = models.ForeignKey(Field)
    owner = models.ForeignKey(User, null=True, blank=True)
    label = models.CharField(max_length=100, blank=True)
    override = models.ForeignKey('self', null=True)
    hidden = models.BooleanField(default=False)
    value = models.TextField()
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    language = models.CharField(max_length=5, blank=True, choices=LANGUAGE_CHOICES)
    group = models.ForeignKey(Group, null=True, blank=True)
    
    def __unicode__(self):
        return "%s=%s" % (self.label, self.value[:20])
    
    @property
    def resolved_label(self):
        if self.label:
            return self.label
        if self.override:
            return self.override.resolved_label
        return self.field.label
    
    def dump(self, owner=None, group=None):
        print("%s: %s" % (self.resolved_label, self.value))

    class Meta:
        order_with_respect_to = 'record'
