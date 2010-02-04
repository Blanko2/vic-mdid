from django.conf import settings as _settings

def settings(request):
    """
    Returns selected context variables based on application settings
    """

    return {
        'STATIC_DIR': _settings.STATIC_DIR,
    }
