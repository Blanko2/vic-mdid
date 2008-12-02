from django import template
from rooibos.storage.models import Media

register = template.Library()

@register.simple_tag
def thumbnail(record):
    media = Media.get_thumbnail_for_record(record)    
    return media and media.get_absolute_url() or ''

@register.inclusion_tag('ui_record.html')
def record(record, selectable=False, selected_records=()):
    media = Media.get_thumbnail_for_record(record)
    return {'record': record,
            'selectable': selectable,
            'selected': record.id in selected_records,
            'thumbnail': media and media.get_absolute_url() or '/static/images/nothumbnail.png'}

@register.inclusion_tag('ui_session_status.html', takes_context=True)
def session_status(context):
    return {'selected': len(context['session'].get('selected_records', ())),
            }