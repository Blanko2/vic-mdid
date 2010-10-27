from django.core.files.uploadhandler import FileUploadHandler, StopUpload
from django.core.cache import cache
from django.db.models import signals
from django.contrib.sites import models as sites_app
from django.contrib.flatpages import models as flatpages_app
from django.contrib.auth import models as auth_app
from django.contrib.comments import models as comments_app
import logging


def create_site_fixtures(*args, **kwargs):
    print "Creating sites fixtures"
    sites_app.Site.objects.get_or_create(
        domain='localhost',
        name='localhost',
    )

def create_flatpage_fixtures(*args, **kwargs):
    print "Creating flatpages fixtures"
    p, created = flatpages_app.FlatPage.objects.get_or_create(
        url='/about/',
        defaults=dict(
            registration_required=0,
            title='About',
            template_name='',
            content='About this site',
            enable_comments=0,
        )
    )
    p.sites.add(sites_app.Site.objects.get(domain='localhost', name='localhost'))

def create_user_fixtures(*args, **kwargs):
    print "Creating auth fixtures"
    auth_app.User.objects.get_or_create(
        username='admin',
        defaults=dict(
            first_name='Admin',
            last_name='Admin',
            is_active=1,
            is_superuser=1,
            is_staff=1,
            password="sha1$bc241$8bc918c29c4d1e313ca858bb1218b6c268b53961",
            email='admin@example.com',
        )
    )

signals.post_syncdb.connect(create_site_fixtures, sender=sites_app)
signals.post_syncdb.connect(create_flatpage_fixtures, sender=flatpages_app)
signals.post_syncdb.connect(create_user_fixtures, sender=auth_app)


def update_record_selection(request):
    if request.method == 'GET':
        was_selected = request.GET.getlist('sr')
        new_selected = request.GET.getlist('r')
    elif request.method == 'POST':
        was_selected = request.POST.getlist('sr')
        new_selected = request.POST.getlist('r')
    else:
        return
    selected = request.session.get('selected_records', ())
    selected = set(selected) - set(map(int, was_selected)) | set(map(int, new_selected))
    request.session['selected_records'] = selected


def clean_record_selection_vars(q):
    q.pop('sr', None)
    q.pop('r', None)
    return q



class UploadProgressCachedHandler(FileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a header or query parameter, 'X-Progress-ID'
    which should contain a unique string to identify the upload to be tracked.
    """

    def __init__(self, request=None, max_length=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.cache_key = None
        self.max_length = max_length
        self.file_too_big = False

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        if 'X-Progress-ID' in self.request.GET :
            self.progress_id = self.request.GET['X-Progress-ID']
        elif 'X-Progress-ID' in self.request.META:
            self.progress_id = self.request.META['X-Progress-ID']
        if self.progress_id:
            self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id )
            cache.set(self.cache_key, {
                'length': self.content_length,
                'uploaded' : 0
            })

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        if self.max_length and self.content_length > self.max_length:
            logging.debug("File '%s' too big (%s>%s), upload aborted" % (file_name, self.content_length, self.max_length))
            raise StopUpload(connection_reset=True)

    def receive_data_chunk(self, raw_data, start):
        if self.cache_key:
            data = cache.get(self.cache_key)
            data['uploaded'] += self.chunk_size
            cache.set(self.cache_key, data)
        return raw_data

    def file_complete(self, file_size):
        pass

    def upload_complete(self):
        if self.cache_key:
            cache.delete(self.cache_key)
