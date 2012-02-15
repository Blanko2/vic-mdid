from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from rooibos.auth import login, authenticate

def basic_challenge(realm = None):
    if realm is None:
        realm = getattr(settings, 'WWW_AUTHENTICATION_REALM', 'Restricted Access')
    # TODO: Make a nice template for a 401 message?
    response =  HttpResponse('Authorization Required', mimetype="text/plain")
    response['WWW-Authenticate'] = 'Basic realm="%s"' % (realm)
    response.status_code = 401
    return response


def basic_authenticate(authentication):
    # Taken from paste.auth
    (authmeth, auth) = authentication.split(' ',1)
    if 'basic' != authmeth.lower():
        return None
    auth = auth.strip().decode('base64')
    username, password = auth.split(':',1)
    return authenticate(username=username, password=password)


class BasicAuthenticationMiddleware:

    def process_request(self, request):
        if request.META.has_key('HTTP_AUTHORIZATION') and not request.user.is_authenticated():
            user = basic_authenticate(request.META['HTTP_AUTHORIZATION'])
            if user is None:
                return basic_challenge()
            else:
                login(request, user)
                request.session['unsafe_logout'] = True

    def process_response(self, request, response):
        if (type(response) == HttpResponseForbidden
            and not request.user.is_authenticated()
            and "CSRF verification failed." not in response.content):
            return basic_challenge()
        else:
            return response
