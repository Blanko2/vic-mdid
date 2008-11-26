from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from models import AccessControl
from . import get_effective_permissions


def access_view(request, app_label, model, object):
    
    model = ContentType.objects.get(app_label=app_label, model=model)
    try:
        object = model.get_object_for_this_type(name=object)
    except ObjectDoesNotExist:
        raise Http404
    (r, w, m) = get_effective_permissions(request.user, object)
    if not m:
        raise Http404    
    rules = AccessControl.objects.filter(content_type__id=model.id, object_id=object.id)
    return render_to_response('access_view.html',
                              {'object': object,
                               'rules': rules,},
                              context_instance=RequestContext(request))
