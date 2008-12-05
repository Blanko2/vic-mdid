from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.forms.models import modelformset_factory
from models import Group, Record, Field, FieldValue
from rooibos.access import filter_by_access, accessible_ids
from rooibos.viewers import get_viewers
from rooibos.storage.models import Media, Storage

def groups(request):    
    groups = filter_by_access(request.user, Group.objects.filter(type='collection'))    
    return render_to_response('data_groups.html',
                              {'groups': groups, },
                              context_instance=RequestContext(request))

def group_raw(request, groupname):
    group = get_object_or_404(filter_by_access(request.user, Group), name=groupname)
    viewers = map(lambda v: v().generate(group), get_viewers('group', 'link'))
    return render_to_response('data_group.html',
                              {'group': group,
                               'viewers': viewers,},
                              context_instance=RequestContext(request))

def record_raw(request, recordname, owner=None, group=None, language=None):
    record = get_object_or_404(Record.objects.filter(name=recordname,
                                                     group__id__in=accessible_ids(request.user, Group)).distinct())
    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))
    contexts = FieldValue.objects.filter(record=record).order_by().distinct().values('owner__username', 'group__name', 'language')        
    contexts = [_clean_context(**c) for c in contexts]
    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'contexts': contexts,
                               'owner': owner,
                               'group': group,
                               'language': language,},
                              context_instance=RequestContext(request))


def _get_fields():
    return Field.objects.select_related('standard').all().order_by('standard', 'name')

def _field_choices():        
    grouped = {}
    for f in _get_fields():
        grouped.setdefault(f.standard and f.standard.title or 'Other', []).append(f)
    return [('', '-' * 10)] + [(g, list((f.id, f.label) for f in grouped[g])) for g in grouped]

class FieldValueForm(forms.ModelForm):

    def clean_field(self):
        if not hasattr(self, '_fields'):
            self._fields = _get_fields()
        data = self.cleaned_data['field']
        return self._fields.get(id=data)
    
    field = forms.ChoiceField(choices=_field_choices())
    
    class Meta:
        model = FieldValue
        exclude = ('override','group','owner')
        

def record_edit(request, recordname, owner=None, group=None, language=''):
    record = get_object_or_404(Record.objects.filter(name=recordname,
                                                     group__id__in=accessible_ids(request.user, Group, write=True)).distinct())    
    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))
    contexts = FieldValue.objects.filter(record=record).order_by().distinct().values('owner__username', 'group__name', 'language')        
    contexts = [_clean_context(**c) for c in contexts]
    
    fieldvalues = record.get_fieldvalues(owner=owner, group=group, language=language)
    print fieldvalues
    FieldValueFormSet = modelformset_factory(FieldValue, form=FieldValueForm,
                                             exclude=FieldValueForm.Meta.exclude, can_order=True, can_delete=True, extra=3)    
    if request.method == 'POST':
        formset = FieldValueFormSet(request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
        if formset.is_valid():
            instances = formset.save()
    else:
        formset = FieldValueFormSet(queryset=fieldvalues, prefix='fv')
    
    return render_to_response('data_record_edit.html',
                              {'record': record,
                               'media': media,
                               'contexts': contexts,
                               'owner': owner,
                               'group': group,
                               'language': language,
                               'fv_formset': formset,},
                              context_instance=RequestContext(request))
    
    
def _clean_context(owner__username, group__name, language):
    c = {}
    c['owner'] = owner__username or '-'
    c['group'] = group__name or '-'
    c['language'] = language or '-'
    if c['owner'] == '-' and c['group'] == '-' and c['language'] == '-':
        c['label'] = 'Default'
    else:
        c['label'] = 'Owner: %s Group: %s Language: %s' % (c['owner'], c['group'], c['language'])
    return c
