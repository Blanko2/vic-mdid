from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.forms.models import modelformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from models import *
from rooibos.presentation.models import Presentation
from rooibos.access import filter_by_access, accessible_ids
#from rooibos.viewers import get_viewers
from rooibos.storage.models import Media, Storage

def groups(request):    
    groups = filter_by_access(request.user, Collection)    
    return render_to_response('data_groups.html',
                              {'groups': groups, },
                              context_instance=RequestContext(request))

def group_raw(request, groupname):
    collection = get_object_or_404(filter_by_access(request.user, Collection), name=groupname)
#    viewers = map(lambda v: v().generate(collection), get_viewers('collection', 'link'))
    return render_to_response('data_group.html',
                              {'collection': collection,
#                               'viewers': viewers,
                               },
                              context_instance=RequestContext(request))

def record_raw(request, recordname, owner=None, collection=None):
    record = get_object_or_404(Record.objects.filter(name=recordname,
                                                     collection__id__in=accessible_ids(request.user, Collection)).distinct())
    media = Media.objects.select_related().filter(record=record, storage__id__in=accessible_ids(request.user, Storage))
    contexts = FieldValue.objects.filter(record=record).order_by().distinct().values('owner__username', 'context_type', 'context_id')        
#    contexts = [_clean_context(**c) for c in contexts]
    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'contexts': contexts,
                               'owner': owner,
                               'collection': collection,},
                              context_instance=RequestContext(request))


def selected_records(request):
    
    selected = request.session.get('selected_records', ())
    records = Record.objects.filter(id__in=selected, collection__id__in=accessible_ids(request.user, Collection))
    
    collections = filter_by_access(request.user, Collection, write=True).values_list('id', 'title')
    presentations = filter_by_access(request.user, Presentation, write=True).values_list('id', 'title')
    
    class AddToCollectionForm(forms.Form):
        collection = forms.ChoiceField(label='Add to collection', choices=[('', 'New Collection'),] + list(collections))
        title = forms.CharField(label='Collection title', max_length=Collection._meta.get_field('title').max_length)
    
    form = AddToCollectionForm()
    
    
    selected = request.session.get('selected_records', ())
    return render_to_response('data_selected_records.html',
                              {'selected': selected,
                               'form': form,
                              },
                              context_instance=RequestContext(request))


@login_required
def record_edit(request, recordname, owner=None, collection=None):

    context = _clean_context(owner, collection)

    if owner and owner != '-':
        owner = get_object_or_404(User, username=owner)
        # cannot edit other user's metadata
        if request.user != owner and not request.user.is_superuser:
            raise Http404
    else:
        owner = None
    if collection and collection != '-':
        # if collection given, must specify user context or have write access to collection
        collection = get_object_or_404(filter_by_access(request.user, Collection, write=(owner != None)))
    else:
        collection = None
        
    if not owner and not collection:
        # no context given, must have write access to a containing collection or be owner (handled below)
        valid_ids = accessible_ids(request.user, Collection, write=True)
    else:
        # context given, must have access to any collection containing the record
        valid_ids = accessible_ids(request.user, Collection)

    record = get_object_or_404(Record.objects.filter(name=recordname, collection__id__in=valid_ids).distinct())
    

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
            cleaned_data['collection'] = collection
            cleaned_data['override'] = self.instance.override
            return cleaned_data
                    
        field = forms.ChoiceField(choices=_field_choices())        
        
        class Meta:
            model = FieldValue
            exclude = ('override',)

    
    if owner or collection:    
        fieldvalues_readonly = record.get_fieldvalues(filter_overridden=True, filter_hidden=True)    
        fieldvalues = record.get_fieldvalues(owner=owner, collection=collection, filter_overridden=True, filter_context=True)
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
                                          override=v, owner=owner, collection=collection)
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
                               'collection': collection,
                               'fv_formset': formset,
                               'fieldvalues': fieldvalues_readonly,},
                              context_instance=RequestContext(request))
    
    
def _clean_context(owner__username, collection__name):
    c = {}
    c['owner'] = owner__username or '-'
    c['collection'] = collection__name or '-'
    if c['owner'] == '-' and c['collection'] == '-':
        c['label'] = 'Default'
    else:
        c['label'] = 'Owner: %s Collection: %s' % (c['owner'], c['collection'])
    return c
