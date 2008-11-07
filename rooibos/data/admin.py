from django.contrib import admin
from models import MetadataStandard, Field

class MetadataStandardAdmin(admin.ModelAdmin):
    pass


class FieldAdmin(admin.ModelAdmin):
    pass


admin.site.register(MetadataStandard, MetadataStandardAdmin)
admin.site.register(Field, FieldAdmin)
