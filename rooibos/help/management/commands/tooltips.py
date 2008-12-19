from django.core.management.base import BaseCommand
import os
import sys
import re
from rooibos.help.models import Tooltip

_tooltip_re = re.compile(r'<!-- Tooltip: (?P<tooltip>.+)-->', re.DOTALL)

class Command(BaseCommand):
    help = 'Updates tooltips from help wiki'

    def handle(self, **options):

        print "Updating tooltips..."
        
        try:        
            cwd = os.getcwd()
            os.chdir(os.path.join(os.path.dirname(__file__), '../..'))  # for wikipedia module
            sys.path.append(os.path.normpath(os.path.join(os.path.dirname(__file__), '../../../../externals/pywikipedia')))
            import wikipedia
            from pagegenerators import AllpagesPageGenerator
            site = wikipedia.getSite()
            ns = filter(lambda k: site.family.namespaces[k].get('_default') == site.family.help_namespace,
                   site.family.namespaces.keys())[0] 
            allpages = AllpagesPageGenerator(namespace=ns, site=site)  
            
            Tooltip.objects.all().delete()
            
            for page in allpages:
                ref = page.titleWithoutNamespace()
                print "\n%s" % ref,
                text = page.get()        
                match = _tooltip_re.search(text)
                if match:
                    tooltip = ' '.join(match.group('tooltip').split())
                    print "= '%s'" % tooltip
                    Tooltip.objects.create(reference=ref, tooltip=tooltip)
            
        finally:
            os.chdir(cwd)
