from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from models import Group, Record
from rooibos.access.views import filter_by_access

def groups(request):    
    groups = filter_by_access(request.user, Group.objects.all())    
    return render_to_response('data_groups.html',
                              {'groups': groups, },
                              context_instance=RequestContext(request))

def group_raw(request, groupname):
    group = get_object_or_404(Group, name=groupname)    
    return render_to_response('data_group.html',
                              {'group': group, },
                              context_instance=RequestContext(request))

def record_raw(request, recordname):
    record = get_object_or_404(Record, name=recordname)    
    return render_to_response('data_record.html',
                              {'record': record, },
                              context_instance=RequestContext(request))