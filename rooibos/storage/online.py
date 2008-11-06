from django.core.files.storage import FileSystemStorage
from django.core.urlresolvers import reverse
import os
import random

class OnlineStorageSystem():

    def __init__(self, base=None):
        pass

    def get_absolute_media_url(self, storage, media):
        return media.url
    
    def get_absolute_file_path(self, storage, media):
        return None
    
    def open(self, name):
        return None
