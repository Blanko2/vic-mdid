from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
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
from rooibos.access import filter_by_access, accessible_ids, check_access
#from rooibos.viewers import get_viewers
from rooibos.storage.models import Media, Storage

def collections(request):    
    collections = filter_by_access(request.user, Collection)    
    return render_to_response('data_groups.html',
                              {'groups': collections, },
                              context_instance=RequestContext(request))

def collection_raw(request, id, name):
    collection = get_object_or_404(filter_by_access(request.user, Collection), id=id)
#    viewers = map(lambda v: v().generate(collection), get_viewers('collection', 'link'))
    return render_to_response('data_group.html',
                              {'collection': collection,
#                               'viewers': viewers,
                               },
                              context_instance=RequestContext(request))


def selected_records(request):
    
    selected = request.session.get('selected_records', ())
    records = Record.objects.filter(id__in=selected, collection__id__in=accessible_ids(request.user, Collection))

    class AddToPresentationForm(forms.Form):
        def available_presentations():
            presentations = list(filter_by_access(request.user, Presentation, write=True).values_list('id', 'title'))
            if request.user.has_perm('data.add_presentation'):
                presentations.insert(0, ('new', 'New Presentation'))
            return presentations
        def clean(self):
            if self.cleaned_data.get("presentation") == 'new' and not self.cleaned_data.get("title"):
                raise forms.ValidationError("Please select an existing presentation or specify a new presentation title")
            return self.cleaned_data
        presentation = forms.ChoiceField(label='Add to presentation', choices=available_presentations())
        title = forms.CharField(label='Presentation title', max_length=Presentation._meta.get_field('title').max_length, required=False)    

    if request.method == "POST":
        presentation_form = AddToPresentationForm(request.POST)
        if presentation_form.is_valid():
            presentation = presentation_form.cleaned_data['presentation']
            title = presentation_form.cleaned_data['title']
            if presentation == 'new':
                if not request.user.has_perm('data.add_presentation'):
                    return HttpResponseForbidden("You are not allowed to create new presentations")
                presentation = Presentation.objects.create(title=title, owner=request.user, hidden=True)
            else:
                presentation = get_object_or_404(filter_by_access(request.user, Presentation, write=True), id=presentation)
            c = presentation.items.count()
            for record in records:
                c += 1
                presentation.items.create(record=record, order=c)
            return HttpResponseRedirect(presentation.get_absolute_url(edit=True))
    else:
        presentation_form = AddToPresentationForm()
    
    return render_to_response('data_selected_records.html',
                              {'selected': selected,
                               'records': records,
                               'presentation_form': presentation_form,
                              },
                              context_instance=RequestContext(request))


@login_required
def record(request, id, name, edit=False):

    record = get_object_or_404(Record.objects.filter(id=id,
                                                     collection__id__in=accessible_ids(request.user, Collection)).distinct())
    media = Media.objects.select_related().filter(record=record,
                                                  storage__id__in=accessible_ids(request.user, Storage),
                                                  master=None)

    if request.user.is_authenticated():
        fieldsets = FieldSet.objects.filter(Q(owner=request.user) | Q(standard=True)).order_by('title')
    else:
        fieldsets = FieldSet.objects.filter(standard=True).order_by('title')
    
    selected_fieldset = request.GET.get('fieldset')
    if selected_fieldset == '_all':
        fieldset = None
    elif selected_fieldset:
        f = fieldsets.filter(name=selected_fieldset)
        if f:
            fieldset = f[0]
        else:
            fieldset = record.fieldset
            selected_fieldset = None            
    else:
        fieldset = record.fieldset
    
    if edit:

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
            
            def clean_field(self):
                if not hasattr(self, '_fields'):
                    self._fields = _get_fields()
                data = self.cleaned_data.get('field')
                return self._fields.get(id=data)

            def clean(self):
                cleaned_data = super(forms.ModelForm, self).clean()
                return cleaned_data
                        
            field = forms.ChoiceField(choices=_field_choices())
            context_type = forms.IntegerField(widget=forms.HiddenInput, required=False)
            context_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
            
            class Meta:
                model = FieldValue
                exclude = []
    
        fieldvalues_readonly = []
        fieldvalues = record.get_fieldvalues()
        
        FieldValueFormSet = modelformset_factory(FieldValue, form=FieldValueForm,
                                                 exclude=FieldValueForm.Meta.exclude, can_delete=True, extra=3)    
        if request.method == 'POST':
            formset = FieldValueFormSet(request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
            if formset.is_valid():
                instances = formset.save(commit=False)
                o1 = fieldvalues and max(v.order for v in fieldvalues) or 0
                o2 = instances and max(v.order for v in instances) or 0
                order = max(o1, o2, 0)
                for instance in instances:                    
                    instance.record = record
                    if instance.order == 0:
                        order += 1
                        instance.order = order
                    instance.save()
                request.user.message_set.create(message="Changes to metadata saved successfully.")
                return HttpResponseRedirect(request.META['PATH_INFO'])
        else:
            formset = FieldValueFormSet(queryset=fieldvalues, prefix='fv')

    else:
        fieldvalues_readonly = record.get_fieldvalues(owner=request.user, fieldset=fieldset)
        formset = None

    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'fieldsets': fieldsets,
                               'selected_fieldset': fieldset,
                               'fieldvalues': fieldvalues_readonly,
                               'fv_formset': formset,
                               'can_edit': check_access(request.user, record, write=True),
                               },
                              context_instance=RequestContext(request))

