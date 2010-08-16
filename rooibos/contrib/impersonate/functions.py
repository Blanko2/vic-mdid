from django.contrib.auth import login
from django.contrib.auth.models import User
from models import Impersonation
from django.db.models import Q
from django.core.exceptions import PermissionDenied
import django.dispatch
import logging
from rooibos.contrib.impersonate import signals

IMPERSONATION_REAL_USER_SESSION_KEY = 'IMPERSONATION_REAL_USER'




def impersonate(request, username):    
    realusername = request.session.get(IMPERSONATION_REAL_USER_SESSION_KEY) or request.user.username    
    if not can_impersonate(realusername, username):
        raise PermissionDenied        
    user = User.objects.get(username=username)
    user.backend = "django.contrib.auth.backends.ModelBackend"
    login(request, user)
    request.session[IMPERSONATION_REAL_USER_SESSION_KEY] = realusername
    signals.user_impersonated.send(sender=None, user=user)  
    logging.debug("Sent user impersonated signal (%s)" % signals.user_impersonated)

def endimpersonation(request):    
    if request.session.has_key(IMPERSONATION_REAL_USER_SESSION_KEY):
        realusername = request.session.get(IMPERSONATION_REAL_USER_SESSION_KEY)
        del request.session[IMPERSONATION_REAL_USER_SESSION_KEY]
        user = User.objects.get(username=realusername)
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)


def get_real_user(request):
    return request.session.get(IMPERSONATION_REAL_USER_SESSION_KEY)


def can_impersonate(realusername, username):
    return User.objects.get(username=realusername).is_superuser or Impersonation.objects.filter(
        Q(users__username=username) | Q(groups__user__username=username),
        group__user__username=realusername).count() > 0
   
    
def get_available_users(realusername):
    if User.objects.get(username=realusername).is_superuser:
        return User.objects.exclude(username=realusername).order_by('username').values_list('username', flat=True)
    else:
        return User.objects.filter(
            Q(impersonated_set__group__user__username=realusername) | Q(groups__impersonated_set__group__user__username=realusername)
            ).distinct().order_by('username').values_list('username', flat=True)