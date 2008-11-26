from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from models import Group, Record
from rooibos.access import filter_by_access, accessible_ids
from rooibos.viewers import get_viewers

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

def record_raw(request, recordname):
    record = Record.objects.filter(name=recordname, group__id__in=accessible_ids(request.user, Group)).distinct()
    if len(record) == 0:
        raise Http404
    return render_to_response('data_record.html',
                              {'record': record[0], },
                              context_instance=RequestContext(request))