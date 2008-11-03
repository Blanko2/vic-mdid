from django.db import models
from django.core.files import File
from rooibos.util.util import unique_slug
from rooibos.data.models import Record
from rooibos.settings import STORAGE_SYSTEMS
import random
import Image

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
            return classobj(base=self.base)
        else:
            return None
    
    def get_absolute_media_url(self, media):
        storage = self._get_storage_system()
        return storage and storage.get_absolute_media_url(self, media) or None

    def get_absolute_file_path(self, media):
        storage = self._get_storage_system()
        return storage and storage.get_absolute_file_path(self, media) or None
    
    def save_file(self, name, content):
        storage = self._get_storage_system()
        return storage and storage.save(name, content) or None

    def load_file(self, name):
        storage = self._get_storage_system()
        return storage and storage.open(name) or None
        

class Media(models.Model):
    record = models.ForeignKey(Record)
    name = models.SlugField(max_length=50)
    url = models.CharField(max_length=1024)
    storage = models.ForeignKey(Storage, null=True)
    mimetype = models.CharField(max_length=128, default='application/binary')
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    bitrate = models.IntegerField(null=True)

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
        return self.storage and self.storage.get_absolute_media_url(self) or self.url

    def get_absolute_file_path(self):
        return self.storage and self.storage.get_absolute_file_path(self) or None

    def save_file(self, name, content):
        if not hasattr(content, 'name'):
            content.name = name
        if not hasattr(content, 'mode'):
            content.mode = 'r'
        if not content is File:
            content = File(content)
        name = self.storage and self.storage.save_file(name, content) or None
        if name:
            self.url = name
            self.identify(save=False)
            self.save()
        else:
            raise IOError("Media file could not be stored")

    def load_file(self):
        return self.storage and self.storage.load_file(self.url) or None

    def identify(self, save=True):
        type = self.mimetype.split('/')[0]
        if type == 'image':
            try:
                im = Image.open(self.get_absolute_file_path())
                (self.width, self.height) = im.size
                if save:
                    self.save()
            except IOError:
                self.width = None
                self.height = None
                self.save()
        elif type == 'video':
            pass
        else:
            pass
