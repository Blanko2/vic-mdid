from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from models import Group, Record, FieldValue
from rooibos.access import filter_by_access, accessible_ids
from rooibos.viewers import get_viewers
from rooibos.storage.models import Media, Storage

def groups(request):    
    groups = filter_by_access(request.user, Group.objects.filter(type='collection'))    
    return render_to_response('data_groups.html',
                              {'groups': groups, },
                              context_instance=RequestContext(request))

def group_raw(request, groupname):
    group = get_object_or_404(filter_by_access(request.user, Group), name=groupname)
    viewers = map(lambda v: v().generate(group), get_viewers('group', 'link'))
    return render_to_response('data_group.html',
                              {'group': group,
                               'viewers': viewers,},
                              context_instance=RequestContext(request))

def record_raw(request, recordname, owner=None, group=None, language=None):
    record = get_object_or_404(Record.objects.filter(name=recordname,
                                                     group__id__in=accessible_ids(request.user, Group)).distinct())
    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))
    contexts = FieldValue.objects.filter(record=record).order_by().distinct().values('owner__username', 'group__name', 'language')
    
    def clean_context(owner__username, group__name, language):
        c = {}
        c['owner'] = owner__username or '-'
        c['group'] = group__name or '-'
        c['language'] = language or '-'
        c['name'] = 'Owner: %s Group: %s Language: %s' % (c['owner'], c['group'], c['language'])
        return c
        
    contexts = [clean_context(**c) for c in contexts]
    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'contexts': contexts,
                               'owner': owner,
                               'group': group,
                               'language': language,},
                              context_instance=RequestContext(request))
