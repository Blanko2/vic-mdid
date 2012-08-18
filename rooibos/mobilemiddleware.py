from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import Context, loader
#from django.conf import settings


# The code for mobile detection was taken from the following pages:
# http://mobiforge.com/developing/story/build-a-mobile-and-desktop-friendly-application-django-15-minutes
# http://www.entzeroth.com/code
class MobileMiddleware:
     
    def process_request(self, request):
        # Check if user is using a mobile device; If so,
        # store it in request
        mobile_uas = [
        'w3c ','acs-','alav','alca','amoi','audi','avan','benq','bird','blac',
        'blaz','brew','cell','cldc','cmd-','dang','doco','eric','hipt','inno',
        'ipaq','java','jigs','kddi','keji','leno','lg-c','lg-d','lg-g','lge-',
        'maui','maxo','midp','mits','mmef','mobi','mot-','moto','mwbp','nec-',
        'newt','noki','oper','palm','pana','pant','phil','play','port','prox',
        'qwap','sage','sams','sany','sch-','sec-','send','seri','sgh-','shar',
        'sie-','siem','smal','smar','sony','sph-','symb','t-mo','teli','tim-',
        'tosh','tsm-','upg1','upsi','vk-v','voda','wap-','wapa','wapi','wapp',
        'wapr','webc','winw','winw','xda','xda-',
        ]
 
        mobile_ua_hints = [ 'SymbianOS', 'Opera Mini', 'iPhone' ]
        ''' Super simple device detection, returns True for mobile devices '''
     
        mobile_browser = False
        ua = request.META['HTTP_USER_AGENT'].lower()[0:4]
     
        if (ua in mobile_uas):
            mobile_browser = True
        else:
            for hint in mobile_ua_hints:
                if request.META['HTTP_USER_AGENT'].find(hint) > 0:
                    mobile_browser = True
                    
        request.is_mobile = mobile_browser
        
         #Set which base template to use
        if request.is_mobile:
            request.urlconf = "rooibos.mobile_urls"
            request.base_template = "master_mobile.html"
        else:
            request.base_template = "master.html"
            
    def process_view(self, request, callback, callback_args, callback_kwargs):
        return None
