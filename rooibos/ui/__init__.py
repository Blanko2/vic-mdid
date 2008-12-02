def update_record_selection(request):
    if request.method == 'GET':
        was_selected = request.GET.getlist('sr')
        new_selected = request.GET.getlist('r')
    elif request.method == 'POST':
        was_selected = request.POST.getlist('sr')
        new_selected = request.POST.getlist('r')
    else:
        return
    selected = request.session.get('selected_records', ())
    selected = set(selected) - set(map(int, was_selected)) | set(map(int, new_selected))
    request.session['selected_records'] = selected
    

def clean_record_selection_vars(q):
    q.pop('sr', None)
    q.pop('r', None)
    return q
