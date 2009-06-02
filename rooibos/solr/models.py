from django.db import models
from django.db.models.signals import post_delete, post_save
from django.contrib.contenttypes.models import ContentType
from rooibos.data.models import Record, Collection, Field
from rooibos.contrib.tagging.models import TaggedItem
from rooibos.util.models import OwnedWrapper
from pysolr import Solr


class SolrIndexUpdates(models.Model):
    record = models.IntegerField()
    delete = models.BooleanField(default=False)




def mark_for_update(record_id, delete=False):
    SolrIndexUpdates.objects.create(record=record_id, delete=delete)

    
def post_record_delete_callback(sender, **kwargs):    
    mark_for_update(record_id=kwargs['instance'].id, delete=True)

def post_record_save_callback(sender, **kwargs):
    mark_for_update(record_id=kwargs['instance'].id)


_record_content_type = ContentType.objects.get_for_model(Record)
_ownedwrapper_content_type = ContentType.objects.get_for_model(OwnedWrapper)

def post_taggeditem_callback(sender, instance, **kwargs):
    if instance.content_type == _ownedwrapper_content_type:
        instance = instance.object
        if instance.content_type == _record_content_type:
            mark_for_update(record_id=instance.object_id)

    
post_delete.connect(post_record_delete_callback, sender=Record)
post_save.connect(post_record_save_callback, sender=Record)

post_delete.connect(post_taggeditem_callback, sender=TaggedItem)
post_save.connect(post_taggeditem_callback, sender=TaggedItem)
