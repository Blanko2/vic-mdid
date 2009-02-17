from django import template
from django.core.urlresolvers import reverse
from rooibos.storage.models import Media
from rooibos.viewers import generate_view_inline
from rooibos.viewers import get_viewers_for_object


register = template.Library()

@register.simple_tag
def view_inline(media):
    return generate_view_inline(media)


@register.inclusion_tag('viewers_list.html')
def list_viewers(obj):
    viewers = []
    for viewer in get_viewers_for_object(obj):
        viewers.append((viewer, hasattr(viewer, 'url_for_obj') and viewer.url_for_obj(obj) or None))
        
    print viewers
    
    return {'obj': obj,
            'viewers': viewers,
            }
