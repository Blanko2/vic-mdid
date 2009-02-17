from django.db import models, connection
from rooibos.data.models import Record
from rooibos.storage.models import Media
from django.contrib.auth.models import User
from rooibos.util import unique_slug
from django.contrib.contenttypes import generic

class Presentation(models.Model):
    
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    owner = models.ForeignKey(User, null=True)
    hidden = models.BooleanField(default=False)
    description = models.TextField(null=True)
    password = models.CharField(max_length=32, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    ownedwrapper = generic.GenericRelation('util.OwnedWrapper')
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Presentation, self).save(kwargs)

    def override_dates(self, created=None, modified=None):
        cursor = connection.cursor()
        if created and self.id:
            cursor.execute("UPDATE %s SET created=%%s WHERE id=%%s" % self._meta.db_table, [created, self.id])
        if modified and self.id:
            cursor.execute("UPDATE %s SET modified=%%s WHERE id=%%s" % self._meta.db_table, [modified, self.id])


class PresentationItem(models.Model):
    
    presentation = models.ForeignKey('Presentation')
    record = models.ForeignKey(Record)
    hidden = models.BooleanField(default=False)
    type = models.CharField(max_length=16, null=True)
    order = models.SmallIntegerField()


class PresentationItemInfo(models.Model):
    
    item = models.ForeignKey('PresentationItem')
    media = models.ForeignKey(Media)
    info = models.TextField(null=True)
