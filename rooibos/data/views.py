from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from models import Group

def group_raw(request, groupname):
    group = get_object_or_404(Group, name=groupname)
    response = HttpResponse(content=group.title)
    return response
