from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context
from rooibos.storage import get_thumbnail_for_record
from rooibos.data.models import Record

register = template.Library()

@register.simple_tag
def thumbnail(record):
    media = get_thumbnail_for_record(record)    
    return media and media.get_absolute_url() or ''

@register.inclusion_tag('ui_record.html')
def record(record, selectable=False, selected_records=()):
    media = get_thumbnail_for_record(record)
    return {'record': record,
            'selectable': selectable,
            'selected': record.id in selected_records,
            'thumbnail': media and media.get_absolute_url() or '/static/images/nothumbnail.png'}

@register.inclusion_tag('ui_record_list.html')
def record_list(record, selectable=False, selected_records=()):
    return {'record': record,
            'selectable': selectable,
            'selected': record.id in selected_records,
            'icon': None or '/static/images/filetypes/none.png'}

@register.inclusion_tag('ui_session_status.html', takes_context=True)
def session_status(context):
    return {'selected': len(context['request'].session.get('selected_records', ())),
            }

def session_status_rendered(context):
    return get_template('ui_session_status.html').render(Context(session_status(context)))


@register.simple_tag
def dir2(var):
    return dir(var)

@register.filter
def scale(value, params):
    try:
        omin, omax, nmin, nmax = map(float, params.split())
        return (value - omin) / (omax - omin) * (nmax - nmin) + nmin
    except:
        return ''
    
@register.tag
def add_selected_records_to_menu(parser, token):
    class Script(template.Node):
        def render(self, context):
            ids = context['request'].session.get('selected_records', ())
            records = Record.objects.filter(id__in=ids)
            return '\n'.join('addSelectedRecord(%s,"%s","%s","%s");' % (r.id, thumbnail(r), r.get_absolute_url(),
                                                                        escape(r.title))
                             for r in records)
    return Script()
