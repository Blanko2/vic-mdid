from django import forms
from django.utils import simplejson
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.cache import cache_control
from django.utils import simplejson
from rooibos.util import json_view
from rooibos.data.models import Record, Collection
from rooibos.storage.models import Storage
from rooibos.access import filter_by_access
from rooibos.contrib.tagging.models import Tag
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper
from rooibos.solr.views import run_search
from rooibos.context_processors import selected_records as ctx_selected_records
from rooibos.presentation.models import Presentation
import random


@cache_control(max_age=24 * 3600)
def css(request, stylesheet):

    return render_to_response(stylesheet + '.css',
                              {},
                              context_instance=RequestContext(request),
                              mimetype='text/css')


def main(request):

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
                              {'records': records,
                               'order': [0] + order},
                              context_instance=RequestContext(request))


@json_view
def select_record(request):
    selected = request.session.get('selected_records', ())
    if request.method == "POST":
        ids = simplejson.loads(request.POST.get('id', '[]'))
        checked = request.POST.get('checked') == 'true'
        if checked:
            selected = set(selected) | set(ids)
        else:
            selected = set(selected) - set(ids)
    request.session['selected_records'] = selected

    context = ctx_selected_records(request)

    return dict(
        basket=render_to_string('ui_basket.html', context),
        header=render_to_string('ui_basket_header.html', context),
        )


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

    storage_manage = filter_by_access(request.user, Storage, manage=True).count() > 0
    storage_write = filter_by_access(request.user, Storage, write=True).count() > 0
    collection_write = filter_by_access(request.user, Collection, write=True).count() > 0
    collection_manage = filter_by_access(request.user, Collection, manage=True).count() > 0

    return render_to_response('ui_management.html',
                              {'storage_manage': storage_manage,
                               'storage_write': storage_write,
                               'collection_write': collection_write,
                               'collection_manage': collection_manage,
                              },
                              context_instance=RequestContext(request))


@login_required
def options(request):
    return render_to_response('ui_options.html',
                              {
                              },
                              context_instance=RequestContext(request))


def clear_selected_records(request):
    request.session['selected_records'] = ()
    return HttpResponseRedirect(request.GET.get('next', reverse('solr-search')))


@login_required
def delete_selected_records(request):

    selected = list(request.session['selected_records'])
    deletable_items = []
    for record in Record.filter_by_access(request.user, *selected):
        if record.editable_by(request.user):
            deletable_items.append(record)

    if request.method == 'POST':
        for record in deletable_items:
            if record.id in selected: selected.remove(record.id)
            record.delete()
        request.session['selected_records'] = selected

        from rooibos.middleware import HistoryMiddleware
        return HttpResponseRedirect(
            request.GET.get('next',
                HistoryMiddleware.go_back(
                    request,
                    to_before=reverse('ui-delete-selected'),
                    default=reverse('solr-selected'))))

    return render_to_response('ui_delete_selected.html',
                              {
                                'items': deletable_items,
                              },
                              context_instance=RequestContext(request))
