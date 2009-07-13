from django.db import models
from django.core.files import File
from django.conf import settings
from django.contrib.auth.models import User
import random
import Image
import os
from rooibos.util import unique_slug, cached_property, clear_cached_properties
from rooibos.data.models import Record
from rooibos.access import sync_access

class Storage(models.Model):
    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50)
    system = models.CharField(max_length=50)
    base = models.CharField(max_length=1024, null=True)
    derivative = models.OneToOneField('self', null=True, related_name='master')
    
    class Meta:
        verbose_name_plural = 'storage'
    
    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Storage, self).save(kwargs)
        
    def __unicode__(self):
        try:
            if self.master:
                return self.name + " (derivative)"
        except:
            pass
        return self.name
    
    def _get_storage_system(self):
        if settings.STORAGE_SYSTEMS.has_key(self.system):
            (modulename, classname) = settings.STORAGE_SYSTEMS[self.system].rsplit('.', 1)
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
    
    def file_exists(self, name):
        storage = self._get_storage_system()
        return storage and storage.exists(name) or False
    
    def get_derivative_storage(self):
        if not self.derivative:
            self.derivative = Storage.objects.create(title=self.title,
                                                     system='local',
                                                     base=os.path.join(settings.SCRATCH_DIR, self.name))
            self.save()        
            sync_access(self, self.derivative)
        return self.derivative
    

class Media(models.Model):
    record = models.ForeignKey(Record)
    name = models.SlugField(max_length=50)
    url = models.CharField(max_length=1024)
    storage = models.ForeignKey(Storage)
    mimetype = models.CharField(max_length=128, default='application/binary')
    width = models.IntegerField(null=True)
    height = models.IntegerField(null=True)
    bitrate = models.IntegerField(null=True)
    master = models.ForeignKey('self', null=True, related_name='derivatives')

    class Meta:
        unique_together = ("record", "name")
        verbose_name_plural = "media"

    def __unicode__(self):
        return self.url

    def save(self, **kwargs):
        unique_slug(self, slug_literal="m-%s" % random.randint(1000000, 9999999),
                    slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Media, self).save(kwargs)
        
    def get_absolute_url(self):
        return self.storage and self.storage.get_absolute_media_url(self) or self.url

    def get_absolute_file_path(self):
        return self.storage and self.storage.get_absolute_file_path(self) or None

    def save_file(self, name, content):
        if not hasattr(content, 'name'):
            content.name = name
        if not hasattr(content, 'mode'):
            content.mode = 'r'
        if not hasattr(content, 'size') and hasattr(content, 'len'):
            content.size = content.len
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
        
    def file_exists(self):
        return self.storage and self.storage.file_exists(self.url) or False

    def identify(self, save=True):
        type = self.mimetype.split('/')[0]
        if type == 'image':
            try:
                im = Image.open(self.get_absolute_file_path())
                (self.width, self.height) = im.size                
            except IOError:
                self.width = None
                self.height = None
            if save:
                self.save()
        elif type == 'video':
            pass
        else:
            pass


class TrustedSubnet(models.Model):
    subnet = models.CharField(max_length=80)
    

class ProxyUrl(models.Model):
    uuid = models.CharField(max_length=36, unique=True)
    subnet = models.ForeignKey(TrustedSubnet)
    url = models.CharField(max_length=1024)
    context = models.CharField(max_length=256, null=True, blank=True)
    user = models.ForeignKey(User)
    user_backend = models.CharField(max_length=256, null=True, blank=True)
    last_access = models.DateTimeField(null=True, blank=True)
    
    def __unicode__(self):
        return 'ProxyUrl %s: %s (Ctx %s, Usr %s, Sbn %s)' % (self.uuid, self.url, self.context, self.user, self.subnet)