from django.conf import settings as _settings
from rooibos.data.models import Record

def settings(request):
    """
    Returns selected context variables based on application settings
    """

    old_vars = (
        'STATIC_DIR',
        'PRIMARY_COLOR',
        'SECONDARY_COLOR',
        'CUSTOM_TRACKER_HTML'
    )
    return dict((var, getattr(_settings, var, ''))
        for var in getattr(_settings, 'EXPOSE_TO_CONTEXT', old_vars))



def selected_records(request):

    selected = request.session.get('selected_records', ())
    if selected:
        unsorted_records = dict(
            (r.id, r)
            for r in Record.filter_by_access(request.user, *selected)[:200])
        # put records back in correct order
        records = []
        for rid in selected:
            if unsorted_records.has_key(rid):
                records.append(unsorted_records[rid])
    else:
        records = None

    return {
        'selected_records_count': len(selected),
        'selected_records': records,
    }
