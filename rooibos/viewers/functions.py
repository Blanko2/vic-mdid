from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
import uuid


class Viewer(object):

    embed_template = 'viewers_embed.html'

    def __init__(self, obj, user, options=None):
        self.user = user
        self.obj = obj
        self.options = options

    def url(self, urltype='shell'):
        kwargs = {
            'viewer': self.name,
            'objid': self.obj.id,
        }
        if urltype == 'shell':
            kwargs['name'] = self.obj.name
        return reverse('viewers-viewer-%s' % urltype, kwargs=kwargs)

    def embed_code(self, request, options):
        return render_to_string(self.embed_template,
                                {
                                    'divid': str(uuid.uuid4())[-12:],
                                    'obj': self.obj,
                                    'options': options,
                                    'request': request,
                                    'url': self.url('script'),
                                })




_registered_viewers = dict()

def discover_viewers():
    if not _registered_viewers:
        for app in settings.INSTALLED_APPS:
            try:
                __import__(app + ".viewers")
            except ImportError:
                pass


def get_registered_viewers():
    discover_viewers()
    return _registered_viewers


def register_viewer(name, cls):
    def register(func):
        _registered_viewers[name] = func
        setattr(cls, 'name', name)
        return func
    return register


def get_viewers_for_object(obj, user):
    viewers = (viewer(obj, user)
               for viewer in get_registered_viewers().values())
    return (viewer for viewer in viewers if viewer)


def get_viewer_by_name(viewer_name):
    return get_registered_viewers().get(viewer_name)
