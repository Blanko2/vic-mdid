import sys, os, re
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from rooibos.help.models import Tooltip

_replace_special = re.compile(r'[^\w]')

def get_tooltip(reference):    
    
    key = 'help_tooltip_' + _replace_special.sub('_', reference)
    tooltip = cache.get(key, None)
    if tooltip:
        return tooltip

    try:
        tooltip = Tooltip.objects.get(reference=reference).tooltip
        cache.set(key, tooltip, 24 * 60 * 60)
        return tooltip
    except ObjectDoesNotExist:
        pass
    
    return "No tooltip available."
