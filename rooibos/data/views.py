from __future__ import with_statement
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.utils import simplejson
from models import *
from rooibos.presentation.models import Presentation
from rooibos.access import filter_by_access, accessible_ids, accessible_ids_list, check_access
#from rooibos.viewers import get_viewers
from rooibos.storage.models import Media, Storage
from rooibos.workers.models import JobInfo
from spreadsheetimport import SpreadsheetImport
import os
import string
import random


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
            if request.user.has_perm('presentation.add_presentation'):
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
                if not request.user.has_perm('presentation.add_presentation'):
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


def record(request, id, name, contexttype=None, contextid=None, contextname=None, edit=False, personal=False):

    writable_collections = list(accessible_ids_list(request.user, Collection, write=True))
    readable_collections = list(accessible_ids_list(request.user, Collection))

    if id and name:
        if request.user.is_superuser:
            q = Q()
        else:
            q = ((Q(owner=request.user) if request.user.is_authenticated() else Q(owner=None)) |
                 Q(collection__id__in=readable_collections))
        record = get_object_or_404(Record.objects.filter(q, id=id).distinct())
        can_edit = check_access(request.user, record, write=True) | \
            accessible_ids(request.user, record.collection_set, write=True).count() > 0
    else:
        record = Record()
        can_edit = len(readable_collections) > 0

    context = None
    if contexttype and contextid:
        app_label, model = contexttype.split('.')
        model_class = get_object_or_404(ContentType, app_label=app_label, model=model).model_class()
        context = get_object_or_404(filter_by_access(request.user, model_class), id=contextid)

    media = Media.objects.select_related().filter(record=record,
                                                  storage__id__in=accessible_ids(request.user, Storage),
                                                  master=None)

    if request.user.is_authenticated():
        fieldsets = FieldSet.objects.filter(Q(owner=request.user) | Q(standard=True)).order_by('title')
    else:
        fieldsets = FieldSet.objects.filter(standard=True).order_by('title')
        edit = False

    selected_fieldset = request.GET.get('fieldset')
    fieldset = None
    if selected_fieldset and selected_fieldset != '_all':
        try:
            fieldset = FieldSet.objects.get(name=selected_fieldset)
        except ObjectDoesNotExist:
            selected_fieldset = None

    if edit:

        if not can_edit and not personal and not context:
            return HttpResponseRedirect(reverse('data-record', kwargs=dict(id=id, name=name)))

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
                cleaned_data = self.cleaned_data
                return cleaned_data

            field = forms.ChoiceField(choices=_field_choices())
            value = forms.CharField(widget=forms.Textarea, required=False)
            context_type = forms.IntegerField(widget=forms.HiddenInput, required=False)
            context_id = forms.IntegerField(widget=forms.HiddenInput, required=False)

            class Meta:
                model = FieldValue
                exclude = []

        class RecordMetadataForm(forms.Form):

            def collection_choices(collections):
                return [(coll.id, coll.title)
                    for coll in Collection.objects.filter(id__in=collections)]

            personal = forms.BooleanField(required=False)
            owner = forms.CharField(required=False)
            collections = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                    choices=collection_choices(writable_collections),
                                                    required=False,
                                                    initial=record.collectionitem_set.values_list('collection_id', flat=True))
            personal_collections = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                                    choices=collection_choices(set(readable_collections) - set(writable_collections)),
                                                    required=False,
                                                    initial=record.collectionitem_set.values_list('collection_id', flat=True))

            def clean_owner(self):
                owner = self.cleaned_data['owner']
                if owner != '' and not User.objects.filter(username=owner).count() > 0:
                    raise forms.ValidationError('%s is not a valid username.' % owner)
                return owner

            def clean_collections(self):
                return map(int, self.cleaned_data['collections'])

            def clean_personal_collections(self):
                return map(int, self.cleaned_data['personal_collections'])

            def clean(self):
                cleaned_data = self.cleaned_data
                personal = cleaned_data.get('personal', False)
                owner = cleaned_data.get('owner', '')
                collections = cleaned_data.get('collections', [])
                if not (personal or owner) and not collections:
                    raise forms.ValidationError('Record must have an owner or belong to at least one collection')
                if owner and not request.user.is_superuser and request.user.username != owner:
                    raise forms.ValidationError('Cannot assign personal images to other users')
                if personal and not owner:
                    cleaned_data['owner'] = request.user.username
                if owner and not personal:
                    cleaned_data['personal'] = True
                if not personal:
                    cleaned_data['personal_collections'] = []
                return cleaned_data

        fieldvalues_readonly = []
        if personal or context:
            fieldvalues = record.get_fieldvalues(owner=request.user, context=context, hidden=True).filter(owner=request.user)
        else:
            fieldvalues = record.get_fieldvalues(hidden=True)

        FieldValueFormSet = modelformset_factory(FieldValue, form=FieldValueForm,
                                                 exclude=FieldValueForm.Meta.exclude, can_delete=True, extra=3)
        if request.method == 'POST':
            formset = FieldValueFormSet(request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
            metadataform = RecordMetadataForm(request.POST) if not (personal or context) else None
            if formset.is_valid() and (personal or context or metadataform.is_valid()):

                if not personal and not context:
                    owner = metadataform.cleaned_data['owner']
                    record.owner = User.objects.get(username=owner) if owner else None
                    record.save()

                    collections = metadataform.cleaned_data['collections'] + metadataform.cleaned_data['personal_collections']
                    toadd = collections
                    for citem in CollectionItem.objects.select_related('collection').filter(
                        record=record, collection__id__in=writable_collections):
                        if not citem.collection.id in collections:
                            citem.delete()
                        else:
                            toadd.remove(citem.collection.id)
                    for id in toadd:
                        CollectionItem.objects.create(record=record, collection_id=id)

                instances = formset.save(commit=False)
                o1 = fieldvalues and max(v.order for v in fieldvalues) or 0
                o2 = instances and max(v.order for v in instances) or 0
                order = max(o1, o2, 0)
                for instance in instances:
                    if not instance.value:
                        if instance.id:
                            instance.delete()
                        continue
                    instance.record = record
                    if instance.order == 0:
                        order += 1
                        instance.order = order
                    if personal or context:
                        instance.owner = request.user
                    if context:
                        instance.context = context
                    instance.save()
                request.user.message_set.create(message="Changes to metadata saved successfully.")
                url = reverse('data-record-edit-personal' if personal else 'data-record-edit',
                              kwargs=dict(id=record.id, name=record.name))
                return HttpResponseRedirect(url)
        else:

            if selected_fieldset:
                needed = fieldset.fields.filter(~Q(id__in=[fv.field_id for fv in fieldvalues])).order_by('fieldsetfield__order').values_list('id', flat=True)
                initial = [{}] * len(fieldvalues) + [{'field': id} for id in needed]
                FieldValueFormSet.extra = len(needed) + 3
            else:
                initial = []

            formset = FieldValueFormSet(queryset=fieldvalues, prefix='fv', initial=initial)
            metadataform = RecordMetadataForm(
                initial={'personal': len(writable_collections) == 0}) if not (personal or context) else None

    else:
        fieldvalues_readonly = record.get_fieldvalues(owner=request.user, fieldset=fieldset)
        formset = None
        metadataform = None

    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'fieldsets': fieldsets,
                               'selected_fieldset': fieldset,
                               'fieldvalues': fieldvalues_readonly,
                               'context': context,
                               'personal': personal,
                               'fv_formset': formset,
                               'metadataform': metadataform,
                               'can_edit': can_edit,
                               },
                              context_instance=RequestContext(request))


def _get_scratch_dir():
    path = os.path.join(settings.SCRATCH_DIR, 'data-import')
    if not os.path.exists(path):
        os.makedirs(path)
    return path    

def _get_filename(request, file):
    return request.COOKIES[settings.SESSION_COOKIE_NAME] + '-' + file

@login_required
def data_import(request):
    
    class UploadFileForm(forms.Form):
        file = forms.FileField()
        
        def clean_file(self):
            file = self.cleaned_data['file']
            if os.path.splitext(file.name)[1] != '.csv':
                raise forms.ValidationError("Please upload a CSV file with a .csv file extension")
            return file

    if request.method == 'POST':        
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            
            filename = "".join(random.sample(string.letters + string.digits, 32))
            dest = open(os.path.join(_get_scratch_dir(), _get_filename(request, filename)), 'wb+')
            for chunk in file.chunks():
                dest.write(chunk)
            dest.close()
            
            return HttpResponseRedirect(reverse('data-import-file', args=(filename,)))
    else:
        form = UploadFileForm()
    
    return render_to_response('data_import.html',
                              {'form': form,
                              },
                              context_instance=RequestContext(request))
    

class DisplayOnlyTextWidget(forms.HiddenInput):
    def render(self, name, value, attrs):
        return super(DisplayOnlyTextWidget, self).render(name, value, attrs) + \
            mark_safe(self.initial if hasattr(self, 'initial') else (value or u''))
    

@login_required
def data_import_file(request, file):
    
    available_collections = filter_by_access(request.user, Collection, write=True)
    if not available_collections:
        raise Http404
    available_fieldsets = FieldSet.objects.filter(Q(owner=None) | Q(owner=request.user))
    
    def _get_fields():
        return Field.objects.select_related('standard').all().order_by('standard', 'name')
    
    def _field_choices():
        grouped = {}
        for f in _get_fields():
            grouped.setdefault(f.standard and f.standard.title or 'Other', []).append(f)
        return [('0', '[do not import]'), ('-1', '[new field]')] + \
               [(g, [(f.id, f.label) for f in grouped[g]]) for g in grouped]
    
    class ImportOptionsForm(forms.Form):
        separator = forms.CharField(required=False)
        collections = forms.MultipleChoiceField(choices=((c.id, c.title) for c in available_collections),
                                                widget=forms.CheckboxSelectMultiple)
        fieldset = forms.ChoiceField(choices=[(0, 'any')] + [(f.id, f.title) for f in available_fieldsets], required=False)
        update = forms.BooleanField(label='Update existing records', initial=True, required=False)
        add = forms.BooleanField(label='Add new records', initial=True, required=False)
        test = forms.BooleanField(label='Test import only', initial=False, required=False)
        
    class MappingForm(forms.Form):
        fieldname = forms.CharField(widget=DisplayOnlyTextWidget)
        mapping = forms.ChoiceField(choices=_field_choices(), required=False)
        separate = forms.BooleanField()

    class BaseMappingFormSet(forms.formsets.BaseFormSet):
        def clean(self):
            if any(self.errors):
                return
            _dcidentifier = Field.objects.get(name='identifier', standard__prefix='dc')
            _identifier_ids = list(_dcidentifier.get_equivalent_fields().values_list('id', flat=True)) + [_dcidentifier.id]
            for i in range(self.total_form_count()):
                if int(self.forms[i].cleaned_data['mapping']) in _identifier_ids:
                    return
            raise forms.ValidationError, "At least one field must be mapped to an identifier field."


    MappingFormSet = formset_factory(MappingForm, extra=0, formset=BaseMappingFormSet)

    def analyze(collections, separator, fieldset):
        try:
            with open(os.path.join(_get_scratch_dir(), _get_filename(request, file)), 'rb') as csvfile:        
                imp = SpreadsheetImport(csvfile, collections, separator=separator, preferred_fieldset=fieldset)
                return imp, imp.analyze()
        except IOError:
            raise Http404()

    if request.method == 'POST':        
        form = ImportOptionsForm(request.POST)
        mapping_formset = MappingFormSet(request.POST, prefix='m')
        if form.is_valid() and mapping_formset.is_valid():
            if request.POST.get('import_button'):
                j = JobInfo.objects.create(owner=request.user,
                                       func='csvimport',
                                       arg=simplejson.dumps(dict(
                                                file=_get_filename(request, file),
                                                separator=form.cleaned_data['separator'],
                                                collections=map(int, form.cleaned_data['collections']),
                                                update=form.cleaned_data['update'],
                                                add=form.cleaned_data['add'],
                                                test=form.cleaned_data['test'],
                                                fieldset=form.cleaned_data['fieldset'],
                                                mapping=dict((f.cleaned_data['fieldname'], int(f.cleaned_data['mapping']))
                                                             for f in mapping_formset.forms),
                                                separate_fields=dict((f.cleaned_data['fieldname'], f.cleaned_data['separate'])
                                                                     for f in mapping_formset.forms),
                                                )
                                       ))
                j.run()
                request.user.message_set.create(message='Import job has been submitted.')
                return HttpResponseRedirect("%s?highlight=%s" % (reverse('workers-jobs'), j.id))
            elif request.POST.get('preview_button'):
                imp, preview_rows = analyze(available_collections.filter(id__in=form.cleaned_data['collections']),
                                       form.cleaned_data['separator'],
                                       available_fieldsets.get(id=form.cleaned_data['fieldset']) if int(form.cleaned_data['fieldset']) else None)
                separator = form.cleaned_data['separator']
        else:
            imp, preview_rows = analyze(None, None, None)
    else:
        imp, preview_rows = analyze(None, None, None)
        mapping_formset = MappingFormSet(initial=[dict(fieldname=f, mapping=v.id if v else 0, separate=True) for f, v in imp.mapping.iteritems()],
                                         prefix='m')
        form = ImportOptionsForm()

    
        
    
    return render_to_response('data_import_file.html',
                              {'form': form,
                               'preview_rows': preview_rows,
                               'mapping_formset': mapping_formset,
                              },
                              context_instance=RequestContext(request))
    