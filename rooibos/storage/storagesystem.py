from django.core.urlresolvers import reverse

class StorageSystem:
    
    def __init__(self, base):
        abstract
    
    def get_absolute_media_url(self, storage, media):
        return reverse('storage-retrieve', args=[media.record.name, media.name])
    