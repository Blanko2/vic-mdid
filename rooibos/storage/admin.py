from django.contrib import admin
from models import Storage

class StorageAdmin(admin.ModelAdmin):
    pass


admin.site.register(Storage, StorageAdmin)
