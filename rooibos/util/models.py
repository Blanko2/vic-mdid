from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group


class OwnedWrapperManager(models.Manager):
    """
    Allows retrieval of a wrapper object by specifying
    """
    def get_for_object(self, user, object):
        obj, created = self.get_or_create(user=user, object_id=object.id,
                                  type=ContentType.objects.get_for_model(object.__class__))
        return obj


class OwnedWrapper(models.Model):
    """
    Used to connect a user to an object, currently used for tagging purposes to
    keep track of tag owners
    """
    type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('type', 'object_id')
    user = models.ForeignKey(User)
    taggeditem = generic.GenericRelation('tagging.TaggedItem')
    
    objects = OwnedWrapperManager()
    
    class Meta:
        unique_together = ('type', 'object_id', 'user')

    @staticmethod
    def t(model):
        return ContentType.objects.get_for_model(model)
