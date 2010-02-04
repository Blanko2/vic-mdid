from django.utils import simplejson
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from rooibos.util import json_view
from rooibos.data.models import Record, Collection
from rooibos.storage.models import Storage
from rooibos.access import accessible_ids, filter_by_access
from rooibos.ui.templatetags.ui import session_status_rendered
from rooibos.contrib.tagging.models import Tag
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper
from rooibos.solr.views import run_search
import random 


@cache_control(max_age=24 * 3600)
def css(request, stylesheet):
    
    return render_to_response(stylesheet + '.css',
                              {},
                              context_instance=RequestContext(request),
                              mimetype='text/css')


def main(request):

    form = AuthenticationForm()
    
    (hits, records, search_facets, orfacet, query, fields) = run_search(
        request.user,
        criteria=['mimetype:image/jpeg'],
        sort='random_%d asc' % random.randint(100000, 999999),
        page=1,
        pagesize=8,
        produce_facets=False)

    order = range(1, 8)
    random.shuffle(order)

    return render_to_response('main.html',
                              {'form': form,
                               'records': records,
                               'order': [0] + order},
                              context_instance=RequestContext(request))


@json_view
def select_record(request):
    selected = request.session.get('selected_records', ())
    if request.method == "POST":
        ids = map(int, request.POST.getlist('id'))
        checked = request.POST.get('checked') == 'true'
        if checked:
            selected = set(selected) | set(ids)
        else:
            selected = set(selected) - set(ids)

    result = []
    records = Record.objects.filter(id__in=selected, collection__id__in=accessible_ids(request.user, Collection))
    for record in records:
        result.append(dict(id=record.id,
                           title=record.title,
                           record_url=record.get_absolute_url(),
                           img_url=record.get_thumbnail_url()))

    request.session['selected_records'] = selected
    return dict(status=session_status_rendered(RequestContext(request)), records=result)


@login_required
def add_tags(request, type, id):
    if request.method <> 'POST':
        return HttpResponseNotAllowed(['POST'])
    tags = parse_tag_input(request.POST.get('tags'))
    ownedwrapper = OwnedWrapper.objects.get_for_object(user=request.user, type=type, object_id=id)
    for tag in tags:
        Tag.objects.add_tag(ownedwrapper, '"%s"' % tag)
    return HttpResponseRedirect(request.GET.get('next') or '/')


@login_required
def remove_tag(request, type, id):
    tag = request.GET.get('tag')
    if request.method == 'POST':
        ownedwrapper = OwnedWrapper.objects.get_for_object(user=request.user, type=type, object_id=id)
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



@json_view
def upload_progress(request):
    """
    Return JSON object with information about the progress of an upload.
    """
    progress_id = ''
    if 'X-Progress-ID' in request.GET:
        progress_id = request.GET['X-Progress-ID']
    elif 'X-Progress-ID' in request.META:
        progress_id = request.META['X-Progress-ID']
    if progress_id:
        return cache.get("%s_%s" % (request.META['REMOTE_ADDR'], progress_id))
    else:
        return {}


@login_required
def manage(request):
    
    storage = filter_by_access(request.user, Storage, manage=True).count() > 0
    
    return render_to_response('ui_management.html',
                              {'storage': storage,
                              },
                              context_instance=RequestContext(request))