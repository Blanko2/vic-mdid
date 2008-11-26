from django import template
from django.core.cache import cache
from django.conf import settings
from django.core.urlresolvers import resolve
from rooibos.help import get_tooltip    
    
register = template.Library()

@register.inclusion_tag("help_pagehelp.html")
def pagehelp(page):
    url = settings.HELP_URL
    return dict(link=url + page)

@register.inclusion_tag("help_help.html")
def help(reference):
    url = settings.HELP_URL
    return dict(link=url + reference, tooltip=get_tooltip(reference))
    

