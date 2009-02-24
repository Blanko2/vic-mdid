from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from rooibos.util import json_view
from rooibos.data.models import Record
from rooibos.storage import get_thumbnail_for_record
from rooibos.access import filter_by_access
from rooibos.ui.templatetags.ui import session_status_rendered

def main(request):
    
    return render_to_response('main.html',
                              {},
                              context_instance=RequestContext(request))


@json_view
def select_record(request):
    ids = map(int, request.POST.getlist('id'))
    checked = request.POST.get('checked') == 'true'
    selected = request.session.get('selected_records', ())
    result = []
    if checked:
        ids = set(ids) - set(selected)
        records = filter_by_access(request.user, Record.objects.filter(id__in=ids))
        for record in records:
            thumb = get_thumbnail_for_record(record)
            selected = set(selected) | set([record.id])
            result.append(dict(id=record.id,
                               title=record.title,
                               record_url=record.get_absolute_url(),
                               img_url=thumb and thumb.get_absolute_url() or ''))
    else:
        selected = set(selected) - set(ids)

    request.session['selected_records'] = selected    
    return dict(status=session_status_rendered(RequestContext(request)), records=result)
