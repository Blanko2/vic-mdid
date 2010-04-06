from django.db import models, connection
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.db.models import Q
from rooibos.data.models import Record
from rooibos.storage.models import Media
from rooibos.util import unique_slug
from rooibos.access import accessible_ids


class Presentation(models.Model):

    title = models.CharField(max_length=100)
    name = models.SlugField(max_length=50, unique=True)
    owner = models.ForeignKey(User)
    hidden = models.BooleanField(default=False)
    source = models.CharField(max_length=1024, null=True)
    description = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=32, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    ownedwrapper = generic.GenericRelation('util.OwnedWrapper')

    def save(self, **kwargs):
        unique_slug(self, slug_source='title', slug_field='name', check_current_slug=kwargs.get('force_insert'))
        super(Presentation, self).save(kwargs)

    def get_absolute_url(self, edit=False):
        return reverse(edit and 'presentation-edit' or 'presentation-view', kwargs={'id': self.id, 'name': self.name})

    def override_dates(self, created=None, modified=None):
        cursor = connection.cursor()
        if created and self.id:
            cursor.execute("UPDATE %s SET created=%%s WHERE id=%%s" % self._meta.db_table, [created, self.id])
        if modified and self.id:
            cursor.execute("UPDATE %s SET modified=%%s WHERE id=%%s" % self._meta.db_table, [modified, self.id])

    def cached_items(self):
        if not hasattr(self, '_cached_items'):
            self._cached_items = tuple(self.items.all())
        return self._cached_items

    def records(self):
        return [i.record for i in self.items.all()]
        
    def visible_item_count(self):
        return self.items.filter(hidden=False).count()

    @staticmethod
    def check_passwords(passwords):
        if passwords:
            q = reduce(lambda a,b: a|b, (Q(id=id, password=password) for id, password in passwords.iteritems()))
            return Presentation.objects.filter(q).values_list('id', flat=True)
        else:
            return []

    def verify_password(self, request):
        self.unlocked = (not self.password) or (request.session.get('passwords', dict()).get(self.id) == self.password)
        return self.unlocked
        
    @staticmethod
    def published_Q(owner=None):
        publish_permission = Permission.objects.get(codename='publish_presentations')
        valid_publishers = User.objects.filter(Q(id__in=publish_permission.user_set.all()) |
                                               Q(groups__id__in=publish_permission.group_set.all()))
        q = Q(owner__in=valid_publishers) & Q(hidden=False)
        if owner:
            return q | Q(owner=owner)
        else:
            return q
        
    @staticmethod
    def get_by_id_for_request(id, request):
        p = Presentation.objects.filter(Presentation.published_Q(request.user),
                                        id=id,
                                        id__in=accessible_ids(request.user, Presentation))
        return p[0] if p and p[0].verify_password(request) else None

    class Meta:
        permissions = (
            ("publish_presentations", "Can publish presentations"),
        )

class PresentationItem(models.Model):

    presentation = models.ForeignKey('Presentation', related_name='items')
    record = models.ForeignKey(Record)
    hidden = models.BooleanField(default=False)
    type = models.CharField(max_length=16, blank=True)
    order = models.SmallIntegerField()

    class Meta:
        ordering = ['order']


class PresentationItemInfo(models.Model):

    item = models.ForeignKey('PresentationItem', related_name='media')
    media = models.ForeignKey(Media)
    info = models.TextField(blank=True)
