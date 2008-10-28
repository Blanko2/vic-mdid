from django.db import models
from rooibos.util.util import unique_slug
from rooibos.data.models import Record
from rooibos.settings import STORAGE_SYSTEMS
import random

class Storage(models.Model):
    title = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    system = models.CharField(max_length=50)
    base = models.CharField(max_length=1024)
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name')
        super(Storage, self).save(kwargs)
        
    def __unicode__(self):
        return self.name
    
    def _get_storage_system(self):
        if STORAGE_SYSTEMS.has_key(self.system):
            (modulename, classname) = STORAGE_SYSTEMS[self.system].rsplit('.', 1)
            module = __import__(modulename)
            for c in modulename.split('.')[1:]:
                module = getattr(module, c)
            classobj = getattr(module, classname)
            return classobj(self.base)
        else:
            return None
    
    def get_absolute_media_url(self, media):
        storage = self._get_storage_system()
        return storage and storage.get_absolute_media_url(self, media) or None


class Media(models.Model):
    record = models.ForeignKey(Record)
    name = models.SlugField(max_length=50)
    url = models.CharField(max_length=1024)
    storage = models.ForeignKey(Storage, null=True)
    mimetype = models.CharField(max_length=128, default='application/binary')
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    bitrate = models.IntegerField(null=True)
    stream = models.BooleanField(null=True)

    class Meta:
        unique_together = ("record", "name")
        verbose_name_plural = "media"

    def __unicode__(self):
        return self.url

    def save(self, **kwargs):
        unique_slug(self, slug_source='_random', slug_field='name')
        super(Media, self).save(kwargs)
        
    def _random_method(self):
        return "m-%s" % random.randint(1000000, 9999999)
    _random = property(_random_method)
    
    def get_absolute_url(self):
        if not self.storage:
            return self.url
        else:
            return self.storage.get_absolute_media_url(self)
