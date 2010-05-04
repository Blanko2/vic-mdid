#from rooibos.viewers import get_viewers
from __future__ import with_statement
from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.forms.util import ErrorList
from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.utils.safestring import mark_safe
from models import *
from rooibos.access import filter_by_access, accessible_ids, accessible_ids_list, check_access
from rooibos.presentation.models import Presentation
from rooibos.storage.models import Media, Storage
from rooibos.userprofile.views import load_settings, store_settings
from rooibos.util import json_view
from rooibos.workers.models import JobInfo
from spreadsheetimport import SpreadsheetImport
import os
import random
import string


def collections(request):
    collections = filter_by_access(request.user, Collection)
    return render_to_response('data_groups.html',
                              {'groups': collections, },
                              context_instance=RequestContext(request))

#def collection_raw(request, id, name):
#    collection = get_object_or_404(filter_by_access(request.user, Collection), id=id)
##    viewers = map(lambda v: v().generate(collection), get_viewers('collection', 'link'))
#    return render_to_response('data_group.html',
#                              {'collection': collection,
##                               'viewers': viewers,
#                               },
#                              context_instance=RequestContext(request))



def record(request, id, name, contexttype=None, contextid=None, contextname=None,
           edit=False, customize=False, personal=False):

    writable_collections = list(accessible_ids_list(request.user, Collection, write=True))
    readable_collections = list(accessible_ids_list(request.user, Collection))
    can_edit = request.user.is_authenticated()
    
    next = request.GET.get('next')

    if id and name:
        if request.user.is_superuser:
            q = Q()
        else:
            q = ((Q(owner=request.user) if request.user.is_authenticated() else Q(owner=None)) |
                 Q(collection__id__in=readable_collections))
        record = get_object_or_404(Record.objects.filter(q, id=id).distinct())
        can_edit = can_edit and (
            # checks if current user is owner:
            check_access(request.user, record, write=True) or
            # or if user has write access to collection:
            accessible_ids(request.user, record.collection_set, write=True).count() > 0)
    else:
        if writable_collections or (personal and readable_collections):
            record = Record()
            if personal:
                record.owner = request.user
        else:
            return HttpResponseForbidden()

    if record.owner:
        valid_collections = set(readable_collections) | set(writable_collections)
    else:
        valid_collections = writable_collections

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

    collection_items = collectionformset = None

    if edit:

        if not can_edit and not customize and not context:
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
                
            def clean_context_type(self):
                context = self.cleaned_data.get('context_type')
                if context:
                    context = ContentType.objects.get(id=context)
                return context

            def clean(self):
                cleaned_data = self.cleaned_data
                return cleaned_data

            field = forms.ChoiceField(choices=_field_choices())
            value = forms.CharField(widget=forms.Textarea, required=False)
            context_type = forms.IntegerField(widget=forms.HiddenInput, required=False)
            context_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
            index_value = forms.CharField(widget=forms.HiddenInput, required=False)

            class Meta:
                model = FieldValue
                exclude = []


        class CollectionForm(forms.Form):
            
            id = forms.IntegerField(widget=forms.HiddenInput)
            title = forms.CharField(widget=DisplayOnlyTextWidget)
            member = forms.BooleanField(required=False)
            shared = forms.BooleanField(required=False)


        fieldvalues_readonly = []
        if customize or context:
            fieldvalues = record.get_fieldvalues(owner=request.user, context=context, hidden=True).filter(owner=request.user)
        else:
            fieldvalues = record.get_fieldvalues(hidden=True)

        FieldValueFormSet = modelformset_factory(FieldValue, form=FieldValueForm,
                                                 exclude=FieldValueForm.Meta.exclude, can_delete=True, extra=3)
        
        CollectionFormSet = formset_factory(CollectionForm, extra=0)
        
        
        if request.method == 'POST':
            formset = FieldValueFormSet(request.POST, request.FILES, queryset=fieldvalues, prefix='fv')
            collectionformset = CollectionFormSet(request.POST, request.FILES, prefix='c') if not (customize or context) else None
            if formset.is_valid() and (customize or context or collectionformset.is_valid()):# or metadataform.is_valid()):
                
                record.save()
                
                if not (customize or context):
                    collections = dict((c['id'],c)
                        for c in collectionformset.cleaned_data
                        if c['id'] in valid_collections)
                    for item in record.collectionitem_set.filter(collection__in=valid_collections):
                        if collections.has_key(item.collection_id):
                            if not collections[item.collection_id]['member']:
                                item.delete()
                            elif collections[item.collection_id]['shared'] == item.hidden:
                                item.hidden = not item.hidden
                                item.save()
                            del collections[item.collection_id]
                    for coll in collections.values():
                        if coll['member']:
                            CollectionItem.objects.create(record=record,
                                                          collection_id=coll['id'],
                                                          hidden=not coll['shared'])

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
                    if customize or context:
                        instance.owner = request.user
                    if context:
                        instance.context = context
                    instance.save()
                request.user.message_set.create(message="Changes to metadata saved successfully.")
                url = next or reverse('data-record-edit-customize' if customize else 'data-record-edit',
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
            if not (customize or context):
                
                collections = dict(
                    ((coll.id, dict(id=coll.id, title=coll.title))
                        for coll in Collection.objects.filter(id__in=valid_collections)
                    )
                )
                
                for item in record.collectionitem_set.all():
                    collections.get(item.collection_id, {}).update(dict(
                        member=True,
                        shared=not item.hidden,
                    ))
                
                collections = sorted(collections.values(), key=lambda c: c['title'])
                
                collectionformset = CollectionFormSet(prefix='c', initial=collections)

    else:
        fieldvalues_readonly = record.get_fieldvalues(owner=request.user, fieldset=fieldset)
        formset = None
        q = Q() if record.owner == request.user or request.user.is_superuser else Q(hidden=False)
        collection_items = record.collectionitem_set.filter(q, collection__in=readable_collections)

    return render_to_response('data_record.html',
                              {'record': record,
                               'media': media,
                               'fieldsets': fieldsets,
                               'selected_fieldset': fieldset,
                               'fieldvalues': fieldvalues_readonly,
                               'context': context,
                               'customize': customize,
                               'fv_formset': formset,
                               'c_formset': collectionformset,
                               'can_edit': can_edit,
                               'next': next,
                               'collection_items': collection_items,
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
    
    available_collections = filter_by_access(request.user, Collection)
    writable_collection_ids = accessible_ids_list(request.user, Collection, write=True)
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
        collections = forms.MultipleChoiceField(choices=((c.id, '%s%s' % ('*' if c.id in writable_collection_ids else '', c.title)) for c in sorted(available_collections, key=lambda c: c.title)),
                                                widget=forms.CheckboxSelectMultiple)
        fieldset = forms.ChoiceField(choices=[(0, 'any')] + [(f.id, f.title) for f in available_fieldsets], required=False)
        update = forms.BooleanField(label='Update existing records', initial=True, required=False)
        add = forms.BooleanField(label='Add new records', initial=True, required=False)
        test = forms.BooleanField(label='Test import only', initial=False, required=False)
        personal = forms.BooleanField(label='Personal records', initial=True, required=False)
        
        def clean(self):
            cleaned_data = self.cleaned_data
            if any(self.errors):
                return cleaned_data
            personal = cleaned_data['personal']
            if not personal:
                for c in map(int, cleaned_data['collections']):
                    if not c in writable_collection_ids:
                        self._errors['collections'] = ErrorList(["Can only add personal records to selected collections"])
                        del cleaned_data['collections']
                        return cleaned_data
            return cleaned_data
        
    class MappingForm(forms.Form):
        fieldname = forms.CharField(widget=DisplayOnlyTextWidget)
        mapping = forms.ChoiceField(choices=_field_choices(), required=False)
        separate = forms.BooleanField(required=False)

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
            
            imp, preview_rows = analyze(available_collections.filter(id__in=form.cleaned_data['collections']),
                       form.cleaned_data['separator'],
                       available_fieldsets.get(id=form.cleaned_data['fieldset']) if int(form.cleaned_data['fieldset']) else None)
            
            store_settings(request.user,
                           'data_import_file_%s' % imp.field_hash,
                           simplejson.dumps(dict(options=form.cleaned_data, mapping=mapping_formset.cleaned_data)))
            
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
                                                personal=form.cleaned_data['personal'],
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
        else:
            imp, preview_rows = analyze(None, None, None)
    else:
        imp, preview_rows = analyze(None, None, None)
        
        # try to load previously stored settings
        key = 'data_import_file_%s' % imp.field_hash
        values = load_settings(request.user, key)
        if values.has_key(key):
            value = simplejson.loads(values[key][0])
            mapping = value['mapping']
            options = value['options']
        else:
            mapping = [dict(fieldname=f, mapping=v.id if v else 0, separate=True)
                       for f, v in imp.mapping.iteritems()]
            options = None
        
        mapping = sorted(mapping, key=lambda m: m['fieldname'])
        
        mapping_formset = MappingFormSet(initial=mapping, prefix='m')
        form = ImportOptionsForm(initial=options)

    return render_to_response('data_import_file.html',
                              {'form': form,
                               'preview_rows': preview_rows,
                               'mapping_formset': mapping_formset,
                               'writable_collections': bool(writable_collection_ids),
                              },
                              context_instance=RequestContext(request))

    
@json_view
def record_preview(request, id):

    readable_collections = list(accessible_ids_list(request.user, Collection))

    if request.user.is_superuser:
        q = Q()
    else:
        q = ((Q(owner=request.user) if request.user.is_authenticated() else Q(owner=None)) |
             Q(collection__id__in=readable_collections))
    record = get_object_or_404(Record.objects.filter(q, id=id).distinct())

    return dict(html=render_to_string('data_previewrecord.html',
                              {'record': record,
                               'none': None,
                               },
                              context_instance=RequestContext(request)))
