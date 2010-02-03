from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.views import login as dj_login, logout as dj_logout
from models import AccessControl, update_membership_by_ip
from . import check_access, get_effective_permissions


def login(request, *args, **kwargs):
    response = dj_login(request, *args, **kwargs)
    if type(response) == HttpResponseRedirect:
        # Successful login, add user to IP based groups
        update_membership_by_ip(request.user, request.META['REMOTE_ADDR'])
    return response


def logout(request, *args, **kwargs):
    if request.session.get('unsafe_logout'):
        return render_to_response('unsafe_logout.html')
    else:
        return dj_logout(request, *args, **kwargs)


def effective_permissions(request, app_label, model, id, name):
    try:
        contenttype = ContentType.objects.get(app_label=app_label, model=model)
        object = contenttype.get_object_for_this_type(id=id)
    except ObjectDoesNotExist:
        raise Http404
    check_access(request.user, object, manage=True, fail_if_denied=True)
    
    username = request.GET.get('user')
    if username:
        acluser = User.objects.filter(username=username)
        if acluser:
            acluser = acluser[0]
            acl = get_effective_permissions(acluser, object)
        else:
            request.user.message_set.create(message="No user with username '%s' exists." % username)
            acl = None
    else:
        acluser = None
        acl = None
        
    return render_to_response('access_effective_permissions.html',
                              {'object': object,
                               'contenttype': contenttype,
                               'acluser': acluser,
                               'acl': acl,
                               'qsuser': username,
                               },
                              context_instance=RequestContext(request))


def modify_permissions(request, app_label, model, id, name):

    try:
        contenttype = ContentType.objects.get(app_label=app_label, model=model)
        object = contenttype.get_object_for_this_type(id=id)
    except ObjectDoesNotExist:
        raise Http404
    check_access(request.user, object, manage=True, fail_if_denied=True)
    
    return render_to_response('access_modify_permissions.html',
                              {'object': object,
                               'contenttype': contenttype,
                               },
                              context_instance=RequestContext(request))
