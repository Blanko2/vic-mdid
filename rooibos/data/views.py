from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.db.models import Q
from django import forms
from django.forms.models import modelformset_factory
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from models import *
from rooibos.presentation.models import Presentation
from rooibos.access import filter_by_access, accessible_ids, accessible_ids_list, check_access
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
        q = (Q(owner=request.user) |
             Q(collection__id__in=readable_collections)
             if not request.user.is_superuser else Q())
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
            fieldvalues = record.get_fieldvalues(owner=request.user, context=context).filter(owner=request.user)
        else:
            fieldvalues = record.get_fieldvalues()

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
