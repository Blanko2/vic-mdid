from django.db import models
from django.db.models import Q
from django.db.models.signals import post_delete, post_save
from ..data.models import Record, Group
from ..settings import SOLR_URL
from pysolr import Solr
from datetime import datetime
import re


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
        conn = Solr(SOLR_URL)
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
    

#post_delete.connect(post_delete_callback, sender=Record)
#post_save.connect(post_save_callback, sender=Record)


class SolrIndex():
    
    def __init__(self):
        self._clean_string_re = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')
    
    def search(self, q, sort=None, start=None, rows=None, facets=None, facet_limit=-1, facet_mincount=0):
        conn = Solr(SOLR_URL)
        result = conn.search(q, sort=sort, start=start, rows=rows, facets=facets, facet_limit=facet_limit, facet_mincount=facet_mincount)
        ids = [int(r['id']) for r in result]
        records = Record.objects.in_bulk(ids)
        return (result.hits, filter(None, map(lambda i: records.get(i), ids)), result.facets)
        
    def clear(self):
        RecordInfo.objects.all().delete()
        conn = Solr(SOLR_URL)
        conn.delete(q='*:*')    
        
    def optimize(self):
        conn = Solr(SOLR_URL)
        conn.optimize()
    
    def index(self, verbose=False):
        self._build_group_tree()
        conn = Solr(SOLR_URL)
        records = Record.objects.filter(recordinfo=None)
        count = 0
        docs = []
        for record in records:
            docs += [self._record_to_solr(record)]
            count += 1
            if len(docs) % 1000 == 0:
                conn.add(docs)
                docs = []
            RecordInfo.objects.create(record=record, last_index=datetime.now())
            if verbose and count % 100 == 0:
                print "\r%s" % count,
        if docs:
            conn.add(docs)
    
        print "\r%s" % count
    
    def _record_to_solr(self, record):
        doc = { 'id': str(record.id) }
        for v in record.fieldvalue_set.all():
            doc[v.field.name + '_t'] = [self._clean_string(v.value)] + (doc.get(v.field.name + '_t') or [])
        parents = record.group_set.values_list('id', flat=True)
        # Combine the direct parents with (great-)grandparents
        doc['groups'] = list(reduce(lambda x,y:set(x)|set(y),[self.parent_groups[p] for p in parents],parents))
        return doc    
    
    def _clean_string(self, s):
        return self._clean_string_re.sub(' ', s)
    
    # A record in a group also belongs to all parent groups
    # This method builds a simple lookup table to quickly find all parent groups
    def _build_group_tree(self):
        self.parent_groups = {}
        for group in Group.objects.all():
            self.parent_groups[group.id] = [g.id for g in group.all_parent_groups]

