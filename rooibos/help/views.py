import sys, os, re
from django.core.cache import cache

tooltip_re = re.compile(r'<!-- Tooltip: (?P<tooltip>.+)-->', re.DOTALL)


# TO DO : wikipedia settings should be pulled from django settings, including name space

def get_tooltip(reference):    
    
    key = 'help_tooltip_' + reference
    tooltip = cache.get(key, None)
    if tooltip:
        return tooltip

    try:
        os.chdir(os.path.dirname(__file__))  # for wikipedia module
        sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../../externals/pywikipedia')))
        import wikipedia
        site = wikipedia.getSite()
        page = wikipedia.Page(site, 'Help v1:' + reference)
        text = page.get()        
        match = tooltip_re.search(text)
        if match:
            tooltip = ' '.join(match.group('tooltip').split())
            cache.set(key, tooltip)
            return tooltip
    except:
        pass
    
    return "No tooltip available."
