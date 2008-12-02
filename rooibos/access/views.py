from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from models import AccessControl
from . import check_access, get_effective_permissions

def access_view(request, app_label, model, object, foruser=None):
    try:
        model = ContentType.objects.get(app_label=app_label, model=model)
        object = model.get_object_for_this_type(name=object)        
    except ObjectDoesNotExist:
        raise Http404
    check_access(request.user, object, manage=True, fail_if_denied=True)
    rules = AccessControl.objects.filter(content_type__id=model.id, object_id=object.id)
    if foruser:
        foruser = get_object_or_404(User, username=foruser)
        foruser_acl = get_effective_permissions(foruser, object)
    else:
        foruser_acl = None
    return render_to_response('access_view.html',
                              {'object': object,
                               'rules': rules,
                               'foruser': foruser,
                               'foruser_acl': foruser_acl,},
                              context_instance=RequestContext(request))
