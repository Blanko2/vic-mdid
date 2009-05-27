from django.utils import simplejson
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from rooibos.util import json_view
from rooibos.data.models import Record, Collection
from rooibos.storage import get_thumbnail_for_record
from rooibos.access import accessible_ids
from rooibos.ui.templatetags.ui import session_status_rendered
from rooibos.contrib.tagging.models import Tag
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper


def main(request):
    
    return render_to_response('main.html',
                              {},
                              context_instance=RequestContext(request))


@json_view
def select_record(request):
    ids = map(int, request.POST.getlist('id'))
    checked = request.POST.get('checked') == 'true'
    selected = request.session.get('selected_records', ())
    if checked:
        selected = set(selected) | set(ids)
    else:        
        selected = set(selected) - set(ids)

    result = []
    records = Record.objects.filter(id__in=selected, collection__id__in=accessible_ids(request.user, Collection))
    for record in records:
        thumb = get_thumbnail_for_record(record)
        result.append(dict(id=record.id,
                           title=record.title,
                           record_url=record.get_absolute_url(),
                           img_url=thumb and thumb.get_absolute_url() or ''))

    request.session['selected_records'] = selected
    return dict(status=session_status_rendered(RequestContext(request)), records=result)


@login_required
def add_tags(request, type, id):
    if request.method <> 'POST':
        return HttpResponseNotAllowed(['POST'])
    tags = parse_tag_input(request.POST.get('tags'))
    ownedwrapper = OwnedWrapper.objects.get_for_object(user=request.user, content_type=type, object_id=id)
    for tag in tags:
        Tag.objects.add_tag(ownedwrapper, '"%s"' % tag)
    return HttpResponseRedirect(request.GET.get('next') or '/')


@login_required
def remove_tag(request, type, id):
    tag = request.GET.get('tag')
    if request.method == 'POST':
        ownedwrapper = OwnedWrapper.objects.get_for_object(user=request.user, content_type=type, object_id=id)
        Tag.objects.update_tags(ownedwrapper,  ' '.join(map(lambda s: '"%s"' % s,
            Tag.objects.get_for_object(ownedwrapper).exclude(name=tag).values_list('name'))))
        if request.is_ajax():
            return HttpResponse(simplejson.dumps(dict(result='ok')), content_type='application/javascript')
        else:
            request.user.message_set.create(message="Tag removed successfully.")
            return HttpResponseRedirect(request.GET.get('next') or '/')
    
    return render_to_response('ui_tag_remove.html',
                              {'tag': tag,
                               'next': request.GET.get('next')},
                              context_instance=RequestContext(request))