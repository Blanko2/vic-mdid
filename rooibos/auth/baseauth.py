from django.contrib.auth.models import User
from random import Random
import string
from models import user_authenticated


class BaseAuthenticationBackend:

    def _create_user(self, username, password=None, first_name=None, last_name=None, email=None):
        password = password or ''.join(Random().sample(string.letters + string.digits, 20))
        last_name = last_name or username
        user = User(username=username, password=password)
        user.first_name = first_name and first_name[:30] or None
        user.last_name = last_name[:30]
        user.email = email
        user.save()
        return user

    def _post_login_check(self, method, user, *args, **kwargs):
        module, method = method.rsplit('.', 1)
        module = __import__(module, globals(), locals(), 'rooibos')
        method = getattr(module, method)
        return method(user, *args, **kwargs)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
