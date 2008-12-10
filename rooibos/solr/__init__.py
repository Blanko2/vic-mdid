from datetime import datetime
import re
from django.conf import settings
from django.db.models import Q
from rooibos.data.models import Record, Group, Field, FieldValue, GroupMembership
from rooibos.storage.models import Media
from pysolr import Solr

SOLR_EMPTY_FIELD_VALUE = 'unspecified'

class SolrIndex():
    
    def __init__(self):
        self._clean_string_re = re.compile('[\x00-\x08\x0b\x0c\x0e-\x1f]')
    
    def search(self, q, sort=None, start=None, rows=None, facets=None, facet_limit=-1, facet_mincount=0, fields=None):
        if not fields:
            fields = ['id']
        elif not 'id' in fields:
            fields.append('id')
        conn = Solr(settings.SOLR_URL)
        result = conn.search(q, sort=sort, start=start, rows=rows,
                             facets=facets, facet_limit=facet_limit, facet_mincount=facet_mincount, fields=fields)
        ids = [int(r['id']) for r in result]
        records = Record.objects.in_bulk(ids)
        return (result.hits, filter(None, map(lambda i: records.get(i), ids)), result.facets)
        
    def clear(self):
        from models import RecordInfo
        RecordInfo.objects.all().delete()
        conn = Solr(settings.SOLR_URL)
        conn.delete(q='*:*')    
        
    def optimize(self):
        conn = Solr(settings.SOLR_URL)
        conn.optimize()
    
    def index(self, verbose=False):
        from models import RecordInfo
        self._build_group_tree()
        conn = Solr(settings.SOLR_URL)
        required_fields = Field.objects.filter(standard__prefix='dc').values_list('name', flat=True)
        count = 0
        batch_size = 1000
        while True:
            records = Record.objects.filter(recordinfo=None)[count:count + batch_size]
            if not records:
                break
            media_dict = self._preload_related(Media, records)
            fieldvalue_dict = self._preload_related(FieldValue, records, related=1)
            groups_dict = self._preload_related(GroupMembership, records, filter=Q(group__type='collection'))
            docs = []
            for record in records:
                docs += [self._record_to_solr(record, required_fields, groups_dict.get(record.id, []),
                                              fieldvalue_dict.get(record.id, []), media_dict.get(record.id, []))]
                count += 1
                if verbose and count % 100 == 0:
                    print "\r%s" % count,
    #            RecordInfo.objects.create(record=record, last_index=datetime.now())
            conn.add(docs)    
        print "\r%s" % count
    
    def _preload_related(self, model, records, filter=Q(), related=0):
        dict = {}
        for x in model.objects.select_related(depth=related).filter(filter, record__in=records):
            dict.setdefault(x.record_id, []).append(x)
        return dict
    
    def _record_to_solr(self, record, required_fields, groups, fieldvalues, media):
        required_fields = dict((f,None) for f in required_fields)
        doc = { 'id': str(record.id) }
        for v in fieldvalues:
            required_fields.pop(v.field.name, None)
            doc.setdefault(v.field.name + '_t', []).append(self._clean_string(v.value))
        for f in required_fields:
            doc[f + '_t'] = SOLR_EMPTY_FIELD_VALUE
        parents = map(lambda gm: gm.group_id, groups)
        # Combine the direct parents with (great-)grandparents
        doc['collections'] = list(reduce(lambda x,y:set(x)|set(y),[self.parent_groups[p] for p in parents],parents))
        if record.owner_id:
            doc['owner'] = record.owner_id
        for m in media:
            doc.setdefault('mimetype', []).append('s%s-%s' % (m.storage_id, m.mimetype))
            doc.setdefault('resolution', []).append('s%s-%s' % (m.storage_id, self._determine_resolution_label(m.width, m.height)))
        return doc    
    
    def _clean_string(self, s):
        return self._clean_string_re.sub(' ', s)
    
    def _determine_resolution_label(self, width, height):
        sizes = ((2400, 'large'), (1600, 'moderate'), (800, 'medium'), (400, 'small'),)
        r = max(width, height)
        if not r: return 'unknown'
        for s, t in sizes:
            if r >= s: return t
        return 'tiny'
    
    # A record in a group also belongs to all parent groups
    # This method builds a simple lookup table to quickly find all parent groups
    def _build_group_tree(self):
        self.parent_groups = {}
        for group in Group.objects.all():
            self.parent_groups[group.id] = [g.id for g in group.all_parent_groups]

