from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
import os
import random

class LocalFileSystemStorageSystem(FileSystemStorage):

    def __init__(self, base=None):
        FileSystemStorage.__init__(self, location=base, base_url=None)

    def get_absolute_media_url(self, storage, media):
        return reverse('storage-retrieve', args=[media.record.name, media.name])
    
    def get_absolute_file_path(self, storage, media):
        return self.path(media.url)        
    
    def get_available_name(self, name):
        (name, ext) = os.path.splitext(name)
        unique = ""
        while True:                
            if not self.exists(name + unique + ext):
                name = name + unique + ext
                break
            if not unique:
                unique = "-1"
            else:
                unique = str(int(unique) - 1)
        return name
    
    def save(self, name, content):
        if not name:
            name = "file" + random.randint(1000000, 9999999)
            print "generated name " + name
        return FileSystemStorage.save(self, name, content)
