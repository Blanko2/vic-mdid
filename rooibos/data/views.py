from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.forms.models import modelformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
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

def record_raw(request, recordname, owner=None, group=None):
    record = get_object_or_404(Record.objects.filter(name=recordname,
                                                     group__id__in=accessible_ids(request.user, Group)).distinct())
    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))
    contexts = FieldValue.objects.filter(record=record).order_by().distinct().values('owner__username', 'group__name')        
    contexts = [_clean_context(**c) for c in contexts]
    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'contexts': contexts,
                               'owner': owner,
                               'group': group,},
                              context_instance=RequestContext(request))


def selected_records(request):
    
    groups = filter_by_access(request.user, Group.objects.exclude(type='folder'), write=True).values_list('id', 'title')
    
    class AddToGroupForm(forms.Form):
        group = forms.ChoiceField(label='Add to group', choices=[('', 'New Group'),] + list(groups))
        title = forms.CharField(label='Group title', max_length=Group._meta.get_field('title').max_length)
    
    form = AddToGroupForm()
    
    
    selected = request.session.get('selected_records', ())
    return render_to_response('data_selected_records.html',
                              {'selected': selected,
                               'form': form,
                              },
                              context_instance=RequestContext(request))


@login_required
def record_edit(request, recordname, owner=None, group=None):

    context = _clean_context(owner, group)

    if owner and owner != '-':
        owner = get_object_or_404(User, username=owner)
        # cannot edit other user's metadata
        if request.user != owner and not request.user.is_superuser:
            raise Http404
    else:
        owner = None
    if group and group != '-':
        # if group given, must specify user context or have write access to group
        group = get_object_or_404(filter_by_access(request.user, Group, write=(owner != None)))
    else:
        group = None
        
    if not owner and not group:
        # no context given, must have write access to a containing collection or be owner (handled below)
        valid_ids = accessible_ids(request.user, Group.objects.filter(type='collection'), write=True)
    else:
        # context given, must have access to any group containing the record
        valid_ids = accessible_ids(request.user, Group)

    record = get_object_or_404(Record.objects.filter(name=recordname, group__id__in=valid_ids).distinct())
    

    def _get_fields():
        return Field.objects.select_related('standard').all().order_by('standard', 'name')
    
    def _field_choices():        
        grouped = {}
        for f in _get_fields():
            grouped.setdefault(f.standard and f.standard.title or 'Other', []).append(f)
        return [('', '-' * 10)] + [(g, [(f.id, f.label) for f in grouped[g]]) for g in grouped]

    class FieldValueForm(forms.ModelForm):
        
        def __init__(self, *args, **kwargs):
            super(FieldValueForm, self).__init__(*args, **kwargs)
            self.is_overriding = (self.instance.override != None)
        
        def clean_field(self):
            if not hasattr(self, '_fields'):
                self._fields = _get_fields()
            data = self.cleaned_data['field']
            return self._fields.get(id=data)

        def clean(self):
            cleaned_data = super(forms.ModelForm, self).clean()
            cleaned_data['owner'] = owner
            cleaned_data['group'] = group
            cleaned_data['override'] = self.instance.override
            return cleaned_data
                    
        field = forms.ChoiceField(choices=_field_choices())        
        
        class Meta:
            model = FieldValue
            exclude = ('override',)

    
    if owner or group:    
        fieldvalues_readonly = record.get_fieldvalues(filter_overridden=True, filter_hidden=True)    
        fieldvalues = record.get_fieldvalues(owner=owner, group=group, filter_overridden=True, filter_context=True)
    else:
        fieldvalues_readonly = []
        fieldvalues = record.get_fieldvalues()
    
    FieldValueFormSet = modelformset_factory(FieldValue, form=FieldValueForm,
                                             exclude=FieldValueForm.Meta.exclude, can_order=True, can_delete=True, extra=3)    
    if request.method == 'POST':
        if request.POST.has_key('override_values'):
            override = map(int, request.POST.getlist('override'))
            for v in fieldvalues_readonly.filter(id__in=override):
                FieldValue.objects.create(record=record, field=v.field, label=v.label, value=v.value, type=v.type,
                                          override=v, owner=owner, group=group)
            return HttpResponseRedirect(request.META['PATH_INFO'])
        else:
            formset = FieldValueFormSet(request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
            if formset.is_valid():
                instances = formset.save(commit=False)
                for instance in instances:
                    instance.record = record
                    instance.save()
                record.set_fieldvalue_order([instance.id for instance in fieldvalues_readonly] +
                                            [form.instance.id for form in formset.ordered_forms])
                return HttpResponseRedirect(request.META['PATH_INFO'])
    else:
        formset = FieldValueFormSet(queryset=fieldvalues, prefix='fv')
    
    return render_to_response('data_record_edit.html',
                              {'record': record,
                               'context': context,
                               'owner': owner,
                               'group': group,
                               'fv_formset': formset,
                               'fieldvalues': fieldvalues_readonly,},
                              context_instance=RequestContext(request))
    
    
def _clean_context(owner__username, group__name):
    c = {}
    c['owner'] = owner__username or '-'
    c['group'] = group__name or '-'
    if c['owner'] == '-' and c['group'] == '-':
        c['label'] = 'Default'
    else:
        c['label'] = 'Owner: %s Group: %s' % (c['owner'], c['group'])
    return c
