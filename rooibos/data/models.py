from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from datetime import datetime
from rooibos.util import unique_slug, cached_property, clear_cached_properties
import random

class Collection(models.Model):
    
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    children = models.ManyToManyField('self', symmetrical=False)
    records = models.ManyToManyField('Record', through='CollectionItem')
    owner = models.ForeignKey(User, null=True)
    hidden = models.BooleanField(default=False)
    description = models.TextField(null=True)
    agreement = models.TextField(null=True)
    password = models.CharField(max_length=32, null=True)
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Collection, self).save(kwargs)
        
    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('data-collection', kwargs={'id': self.id, 'name': self.name})
    
    @property
    def all_child_collections(self):
        sub = list(self.children.all())
        result = ()
        while True:
            todo = ()
            for collection in sub:
                if self != collection:
                    result += (collection,)
                for g in collection.children.all():
                    if g != self and not g in sub:
                        todo += (g,)
            if not todo:
                break
            sub = todo            
        return result
    
    @property
    def all_parent_collections(self):
        parents = list(self.collection_set.all())
        result = ()
        while True:
            todo = ()
            for collection in parents:
                if self != collection:
                    result += (collection,)
                for g in collection.collection_set.all():
                    if g != self and not g in parents:
                        todo += (g,)
            if not todo:
                break
            sub = todo            
        return result
            
    @property
    def all_records(self):
        return Record.objects.filter(collection__in=self.all_child_collections + (self,)).distinct()


class CollectionItem(models.Model):
    collection = models.ForeignKey('Collection')
    record = models.ForeignKey('Record')
    hidden = models.BooleanField(default=False)


class Record(models.Model):
    created = models.DateTimeField(default=datetime.now())
    modified = models.DateTimeField(auto_now=True)
    name = models.SlugField(max_length=50, unique=True)
    parent = models.ForeignKey('self', null=True)
    source = models.CharField(max_length=1024, null=True)
    manager = models.CharField(max_length=50, null=True)
    next_update = models.DateTimeField(null=True)
    owner = models.ForeignKey(User, null=True)
    fieldset = models.ForeignKey('FieldSet', null=True)
    
    def __unicode__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('data-record', kwargs={'id': self.id, 'name': self.name})

    def save(self, **kwargs):
        unique_slug(self, slug_literal='r-%s' % random.randint(1000000, 9999999),
                    slug_field='name', check_current_slug=kwargs.get('force_insert'))
        self._clear_cached_items()
        super(Record, self).save(kwargs)
        
    def get_fieldvalues(self, owner=None, context=None,
                        filter_overridden=False, filter_hidden=False, filter_context=False):
        q_context = context and Q(context_type=ContentType.objects.get_for_model(context.__class__),
                                  context_id=context.id) \
                            or Q()
        if not filter_context:
            q_context = q_context | Q(context_type=None, context_id=None)
        
        q_owner = Q(owner=owner)
        if not filter_context:
            q_owner = q_owner | Q(owner=None)
        
        values = self.fieldvalue_set.filter(q_context, q_owner)
        remove = []
        for v in values:
            if filter_overridden and v.override_id:
                remove.append(v.override_id)
            if filter_hidden and v.hidden:
                remove.append(v.id)
        return values.exclude(id__in=remove)
    
    def dump(self, owner=None, collection=None):
        print("Created: %s" % self.created)
        print("Modified: %s" % self.modified)
        print("Name: %s" % self.name)
        for v in self.fieldvalue_set.all():
            v.dump(owner, collection)

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
    TYPE_CHOICES = (
        ('T', 'Text'),
        ('D', 'Date'),
        ('N', 'Numeric'),
    )
    label = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)
    standard = models.ForeignKey(MetadataStandard, null=True, blank=True)
    equivalent = models.ManyToManyField("self", null=True, blank=True)

    def save(self, **kwargs):
        unique_slug(self, slug_source='label', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Field, self).save(kwargs)

    @property
    def full_name(self):
        if self.standard:
            return "%s:%s" % (self.standard.prefix, self.name)
        else:
            return self.name
    
    def __unicode__(self):
        return self.full_name
    
    class Meta:
        unique_together = ('name', 'standard')
        ordering = ['name']
        order_with_respect_to = 'standard'
    

class FieldSet(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    fields = models.ManyToManyField(Field, through='FieldSetField')
    owner = models.ForeignKey(User, null=True, blank=True)    
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='label', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(FieldSet, self).save(kwargs)
        
    def __unicode__(self):
        return self.title


class FieldSetField(models.Model):
    fieldset = models.ForeignKey(FieldSet)
    field = models.ForeignKey(Field)
    order = models.IntegerField(default=0)
    importance = models.SmallIntegerField(default=1)
    
    def __unicode__(self):
        return self.field.__unicode__()
    
    class Meta:
        ordering = ['order']
    
    
class FieldValue(models.Model):
    record = models.ForeignKey(Record, editable=False)
    field = models.ForeignKey(Field)
    owner = models.ForeignKey(User, null=True, blank=True)
    label = models.CharField(max_length=100, blank=True)
    override = models.ForeignKey('self', null=True, blank=True)
    hidden = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    value = models.TextField()
    date_start = models.DateTimeField(null=True, blank=True)
    date_end = models.DateTimeField(null=True, blank=True)
    numeric_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    language = models.CharField(max_length=5, blank=True)
    context_type = models.ForeignKey(ContentType, null=True)
    context_id = models.PositiveIntegerField(null=True)
    context = generic.GenericForeignKey('context_type', 'context_id')
        
    def __unicode__(self):
        return "%s=%s" % (self.label, self.value[:20])
    
    @property
    def resolved_label(self):
        if self.label:
            return self.label
        if self.override:
            return self.override.resolved_label
        return self.field.label
    
    def dump(self, owner=None, collection=None):
        print("%s: %s" % (self.resolved_label, self.value))

    class Meta:
        order_with_respect_to = 'record'
