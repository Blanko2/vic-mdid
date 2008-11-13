from django import template
from rooibos.storage.models import Media
from rooibos.viewers.views import generate_view_inline

register = template.Library()

@register.simple_tag
def view_inline(media):
    return generate_view_inline(media)
