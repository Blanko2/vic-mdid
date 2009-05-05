import re
from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable
from rooibos.contrib.tagging.models import Tag
from rooibos.storage import get_thumbnail_for_record
from rooibos.data.models import Record
from rooibos.util.models import OwnedWrapper

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


class OwnedTagsForObjectNode(template.Node):
    def __init__(self, object, user, var_name):
        self.object = object
        self.user = user
        self.var_name = var_name
    def render(self, context):
        ownedwrapper = OwnedWrapper.objects.get_for_object(self.user.resolve(context), self.object.resolve(context))
        context[self.var_name] = Tag.objects.get_for_object(ownedwrapper)
        return ''
    
@register.tag
def owned_tags_for_object(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) for (.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    object, user, var_name = m.groups()
    return OwnedTagsForObjectNode(Variable(object), Variable(user), var_name)
