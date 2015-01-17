from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group


class OwnedWrapperManager(models.Manager):
    """
    Allows retrieval of a wrapper object by specifying
    """
    def get_for_object(self, user, object=None, type=None, object_id=None):
        try:
            type = int(type)
        except TypeError:
            pass

        obj, created = self.get_or_create(
            user=user,
            object_id=object and object.id or object_id,
            content_type=object and OwnedWrapper.t(object.__class__) or type)
        return obj


class OwnedWrapper(models.Model):
    """
    Used to connect a user to an object, currently used for tagging purposes to
    keep track of tag owners
    """
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User)
    taggeditem = generic.GenericRelation('tagging.TaggedItem')

    objects = OwnedWrapperManager()

    class Meta:
        unique_together = ('content_type', 'object_id', 'user')

    @staticmethod
    def t(model):
        return ContentType.objects.get_for_model(model)
