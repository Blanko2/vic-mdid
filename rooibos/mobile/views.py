from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def m_main(request):
    print '** blah!!'
    form = AuthenticationForm()
    request.session.set_test_cookie()
    return render_to_response('m_login.html', {'form': form}, context_instance=RequestContext(request))

