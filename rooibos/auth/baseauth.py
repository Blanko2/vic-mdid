from django.contrib.auth.models import User
from django.conf import settings
from random import Random
import string


class BaseAuthenticationBackend:

    def _create_user(self, username, password=None, first_name=None, last_name=None, email=None):
        password = password or ''.join(Random().sample(string.letters + string.digits, 20))
        last_name = last_name or username
        user = User(username=username, password=password)
        user.first_name = first_name and first_name[:30] or ''
        user.last_name = last_name[:30]
        user.email = email
        user.save()
        return user

    def _post_login_check(self, user, info=None):
        for check in settings.LOGIN_CHECKS:
            module, method = check.rsplit('.', 1)
            module = __import__(module, globals(), locals(), 'rooibos')
            method = getattr(module, method)
            if not method(user, info):
                return False
        return True

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
