from django.db import models
from django.db.models.signals import post_delete, post_save
from rooibos.data.models import Record, Collection, Field
from django.conf import settings
from pysolr import Solr

class RecordInfo(models.Model):
    record = models.OneToOneField(Record)
    last_index = models.DateTimeField(null=True)
    

DISABLE_SOLR_UPDATES = False

def DisableSolrUpdates():
    DISABLE_SOLR_UPDATES = True
    
def EnableSolrUpdates():
    DISABLE_SOLR_UPDATES = False


def post_delete_callback(sender, **kwargs):
    if DISABLE_SOLR_UPDATES:
        return
    try:
        id = kwargs['instance'].id
        RecordInfo.objects.filter(record__id=id).delete()
        conn = Solr(settings.SOLR_URL)
        conn.delete(id=str(id))
    except:
        pass
    
def post_save_callback(sender, **kwargs):
    if DISABLE_SOLR_UPDATES:
        return
    try:
        id = kwargs['instance'].id
        RecordInfo.objects.filter(record__id=id).delete()
    except:
        pass
    
# TODO: optimize and connect post_save/delete

#post_delete.connect(post_delete_callback, sender=Record)
#post_save.connect(post_save_callback, sender=Record)
