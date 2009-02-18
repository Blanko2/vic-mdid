from django import template
from django.core.urlresolvers import reverse
from rooibos.storage.models import Media
from rooibos.viewers import get_viewers_for_object


register = template.Library()

@register.simple_tag
def view_inline(obj):
    viewers = get_viewers_for_object(obj, inline=True)
    # Todo: don't just pick first one
    return viewers and viewers[0].inline(obj) or ''


@register.inclusion_tag('viewers_list.html')
def list_viewers(obj):
    viewers = []
    for viewer in get_viewers_for_object(obj):
        viewers.append((viewer, hasattr(viewer, 'url_for_obj') and viewer.url_for_obj(obj) or None))
        
    return {'obj': obj,
            'viewers': viewers,
            }
