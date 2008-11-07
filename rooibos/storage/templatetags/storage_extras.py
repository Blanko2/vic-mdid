from django import template
from rooibos.storage.models import Media

register = template.Library()

@register.simple_tag
def thumbnail(record):
    media = Media.get_thumbnail_for_record(record)    
    return media and media.get_absolute_url() or ''

