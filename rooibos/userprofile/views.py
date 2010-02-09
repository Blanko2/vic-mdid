from django.views.decorators.cache import cache_control
from rooibos.util import json_view
from models import UserProfile, Preference


@json_view
def load_settings(request, filter=None):
    if not request.user.is_authenticated():
        return dict(error='Not logged in')
    try:
        profile = request.user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    settings = dict()
    if filter:
        preferences = profile.preferences.filter(setting__startswith=filter)
    else:
        preferences = profile.preferences.all()
    for setting in preferences:
        settings.setdefault(setting.setting, ()).append(setting.value)
    return dict(settings=settings)
    

@json_view
def store_settings(request):
    if not request.user.is_authenticated():
        return dict(error='Not logged in')        
    try:
        profile = request.user.get_profile()
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    key = request.POST.get('key')
    value = request.POST.get('value')
    
    if key and value:
        setting, created = profile.preferences.get_or_create(setting=key)
        setting.value = value
        setting.save()
        return dict(message='Saved')
        
    return dict(message='No key/value provided')
