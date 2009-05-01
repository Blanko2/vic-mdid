from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context
from rooibos.storage import get_thumbnail_for_record
from rooibos.data.models import Record

register = template.Library()

@register.inclusion_tag('ui_record.html', takes_context=True)
def record(context, record, selectable=False):
    return {'record': record,
            'selectable': selectable,
            'selected': record.id in context['request'].session.get('selected_records', ()),
            }

@register.inclusion_tag('ui_record_list.html', takes_context=True)
def record_list(context, record, selectable=False):
    return {'record': record,
            'selectable': selectable,
            'selected': record.id in context['request'].session.get('selected_records', ()),
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
        return (float(value) - omin) / (omax - omin) * (nmax - nmin) + nmin
    except:
        return ''
