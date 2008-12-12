import sys, os, re
from django.core.cache import cache

_tooltip_re = re.compile(r'<!-- Tooltip: (?P<tooltip>.+)-->', re.DOTALL)

def get_tooltip(reference):    
    
    key = 'help_tooltip_' + reference
    tooltip = cache.get(key, None)
    if tooltip:
        return tooltip

    try:        
        cwd = os.getcwd()
        os.chdir(os.path.dirname(__file__))  # for wikipedia module
        sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../../externals/pywikipedia')))
        import wikipedia        
        site = wikipedia.getSite()
        page = wikipedia.Page(site, '%s:%s' % (site.family.help_namespace, reference))
        text = page.get()        
        match = _tooltip_re.search(text)
        if match:
            tooltip = ' '.join(match.group('tooltip').split())
            cache.set(key, tooltip, 24 * 60 * 60)
            return tooltip
    except Exception, e:
        print e
        pass
    finally:
        os.chdir(cwd)
    
    return "No tooltip available."
