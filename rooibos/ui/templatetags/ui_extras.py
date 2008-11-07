from django import template
from rooibos.storage.models import Media
from rooibos.ui.viewers import generate_inlineviewer

register = template.Library()

@register.simple_tag
def inlineview(media):
    return generate_inlineviewer(media)
