import re
from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable, Template
from django.contrib.contenttypes.models import ContentType
from rooibos.contrib.tagging.models import Tag
from rooibos.data.models import Record
from rooibos.util.models import OwnedWrapper

register = template.Library()

@register.inclusion_tag('ui_record.html', takes_context=True)
def record(context, record, selectable=False, viewmode="thumb"):
    return {'record': record,
            'selectable': selectable,
            'selected': record.id in context['request'].session.get('selected_records', ()),
            'viewmode': viewmode,
            }


def session_status_rendered(context):    
    t = Template('{% load humanize %}{{ selected|intcomma }} record{{ selected|pluralize }} selected')
    c = Context(dict(selected = len(context['request'].session.get('selected_records', ()))))
    return t.render(c)


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
    def __init__(self, object, user, var_name, include=True):
        self.object = object
        self.user = user
        self.var_name = var_name
        self.include = include
    def render(self, context):
        object = self.object.resolve(context)
        user = self.user.resolve(context)
        if self.include:
            ownedwrapper = OwnedWrapper.objects.get_for_object(user, object)
            context[self.var_name] = Tag.objects.get_for_object(ownedwrapper)
        else:
            qs = OwnedWrapper.objects.filter(object_id=object.id, content_type=OwnedWrapper.t(object.__class__)) 
            if not user.is_anonymous():
                qs = qs.exclude(user=user)                
            context[self.var_name] = Tag.objects.cloud_for_queryset(qs)
        return ''
    
@register.tag
def owned_tags_for_object(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) (for|except) (.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    object, rule, user, var_name = m.groups()
    return OwnedTagsForObjectNode(Variable(object), Variable(user), var_name, rule == 'for')


@register.inclusion_tag('ui_tagging_form.html', takes_context=True)
def add_tags_form(context, object):
    return {'object_id': object.id,
            'object_type': ContentType.objects.get_for_model(object.__class__).id,
            'request': context['request'],
            }


@register.inclusion_tag('ui_tag.html', takes_context=True)
def tag(context, tag, object=None, removable=False, styles=None):
    return {'object_id': object and object.id or None,
            'object_type': object and ContentType.objects.get_for_model(object.__class__).id or None,
            'tag': tag,
            'removable': removable,
            'styles': styles,
            'request': context['request'],
            }
