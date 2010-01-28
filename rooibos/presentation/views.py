from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory
from django.db.models.aggregates import Count
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import backend
from django import forms
from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.contrib.tagging.forms import TagField
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper
from rooibos.access import filter_by_access, accessible_ids
from rooibos.ui.forms import SplitTaggingField
from rooibos.util import json_view
from rooibos.storage.models import ProxyUrl
from models import Presentation, PresentationItem
import logging


@login_required
def manage(request):

    tags = request.GET.getlist('tag')
    querystring = request.GET.urlencode()

    existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                    filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))

    class ManagePresentationsForm(forms.Form):
       tags = SplitTaggingField(label='Tags',
                                choices=[(t, t) for t in existing_tags],
                                required=False,
                                add_label='Additional tags')
       mode = forms.ChoiceField(label='Action',
                                required=True,
                                choices=[('add', 'Add to existing tags'), ('replace', 'Replace existing tags')],
                                initial='add')

    if request.method == "POST":
        ids = map(int, request.POST.getlist('h'))
        if request.POST.get('hide') or request.POST.get('unhide'):
            hide = request.POST.get('hide') or False
            for presentation in Presentation.objects.filter(owner=request.user, id__in=ids):
                presentation.hidden = hide
                presentation.save()
            return HttpResponseRedirect(reverse('presentation-manage') + '?' + querystring)

        if request.POST.get('delete'):
            Presentation.objects.filter(owner=request.user, id__in=ids).delete()

        form = ManagePresentationsForm(request.POST)
        if form.is_valid():
            replace = form.cleaned_data['mode'] == 'replace'
            for presentation in Presentation.objects.filter(owner=request.user, id__in=ids):
                if replace:
                    Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                            form.cleaned_data['tags'])
                else:
                    for tag in parse_tag_input(form.cleaned_data['tags']):
                        Tag.objects.add_tag(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                            '"%s"' % tag)
            return HttpResponseRedirect(reverse('presentation-manage') + '?' + querystring)
    else:
        form = ManagePresentationsForm()

    if tags:
        qs = OwnedWrapper.objects.filter(user=request.user, content_type=OwnedWrapper.t(Presentation))
        ids = list(TaggedItem.objects.get_by_model(qs, tags).values_list('object_id', flat=True))
        presentations = Presentation.objects.annotate(item_count=Count('items')).filter(owner=request.user, id__in=ids).order_by('title')
    else:
        presentations = Presentation.objects.annotate(item_count=Count('items')).filter(owner=request.user).order_by('title')

    tag_filter = " and ".join(tags)

    tags = Tag.objects.cloud_for_model(OwnedWrapper, steps=5,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))

    return render_to_response('presentation_manage.html',
                          {'tags': tags,
                           'tagobjects': Tag.objects,
                           'presentations': presentations,
                           'querystring': querystring,
                           'tag_filter': tag_filter,
                           'form': form,
                           },
                          context_instance=RequestContext(request))



@login_required
def create(request):

    existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))

    selected = request.session.get('selected_records', ())
    next = request.GET.get('next', '') or reverse('presentation-manage')

    class CreatePresentationForm(forms.Form):
        title = forms.CharField(label='Title', max_length=Presentation._meta.get_field('title').max_length)
        tags = SplitTaggingField(label='Tags', choices=[(t, t) for t in existing_tags],
                    required=False, add_label='Additional tags')
        add_selected = forms.BooleanField(label='Add selected records immediately', required=False, initial=True)

    if request.method == "POST":
        form = CreatePresentationForm(request.POST)
        if form.is_valid():
            presentation = Presentation.objects.create(title=form.cleaned_data['title'],
                                                       owner=request.user)
            if form.cleaned_data['add_selected']:
                for order,record in enumerate(selected):
                    PresentationItem.objects.create(presentation=presentation, record_id=record, order=order)
                request.session['selected_records'] = ()
            Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                    form.cleaned_data['tags'])
            return HttpResponseRedirect(next)
    else:
        form = CreatePresentationForm()

    return render_to_response('presentation_create.html',
                          {'form': form,
                           'next': next,
                           'selected': selected,
                           },
                          context_instance=RequestContext(request))


@login_required
def edit(request, id, name):

    presentation = get_object_or_404(Presentation.objects.filter(
        id=id, id__in=accessible_ids(request.user, Presentation, write=True, manage=True)))
    existing_tags = [t.name for t in Tag.objects.usage_for_model(
        OwnedWrapper, filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))]
    tags = Tag.objects.get_for_object(
        OwnedWrapper.objects.get_for_object(user=request.user, object=presentation))

    class PropertiesForm(forms.Form):
        title = forms.CharField(label='Title', max_length=Presentation._meta.get_field('title').max_length)
        tags = SplitTaggingField(label='Tags', choices=[(t, t) for t in existing_tags],
                                         required=False, add_label='Additional tags')
        hidden = forms.BooleanField(label='Hidden', required=False)
        description = forms.CharField(label='Description', widget=forms.Textarea, required=False)
        password = forms.CharField(label='Password', required=False,
                                   max_length=Presentation._meta.get_field('password').max_length)

    if request.method == "POST":
        form = PropertiesForm(request.POST)
        if form.is_valid():
            presentation.title = form.cleaned_data['title']
            presentation.name = None
            presentation.hidden = form.cleaned_data['hidden']
            presentation.description = form.cleaned_data['description']
            presentation.password = form.cleaned_data['password']
            presentation.save()
            Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                    form.cleaned_data['tags'])
            return HttpResponseRedirect(reverse('presentation-edit', kwargs={'id': presentation.id, 'name': presentation.name}))
    else:
        form = PropertiesForm(initial={'title': presentation.title,
                               'hidden': presentation.hidden,
                               'tags': tags,
                               'description': presentation.description,
                               'hidden': presentation.hidden,
                               })

    return render_to_response('presentation_properties.html',
                      {'presentation': presentation,
                       'form': form,},
                      context_instance=RequestContext(request))


@login_required
def items(request, id, name):

    presentation = get_object_or_404(Presentation.objects.filter(
        id=id, id__in=accessible_ids(request.user, Presentation, write=True, manage=True)))

    OrderingFormSet = modelformset_factory(PresentationItem, extra=0, can_delete=True, exclude=('record','presentation'))
    if request.method == 'POST':
        formset = OrderingFormSet(request.POST, queryset=presentation.items.all())
        if formset.is_valid():
            formset.save()
            request.user.message_set.create(message="Changes to presentation items saved successfully.")
            return HttpResponseRedirect(reverse('presentation-items', kwargs={'id': presentation.id, 'name': presentation.name}))
    else:
        formset = OrderingFormSet(queryset=presentation.items.all())

    contenttype = ContentType.objects.get_for_model(Presentation)

    return render_to_response('presentation_items.html',
                      {'presentation': presentation,
                       'presentation_contenttype': "%s.%s" % (contenttype.app_label, contenttype.model),
                       'formset': formset,},
                      context_instance=RequestContext(request))



def view(request, id, name):

    presentation = get_object_or_404(Presentation.objects.filter(
        id=id, id__in=accessible_ids(request.user, Presentation)))

    return_url = request.GET.get('next', reverse('presentation-browse'))
    
    return render_to_response('presentation_mediaviewer.html',
                              {'presentation': presentation,
                               'return_url': return_url,
                            },
                        context_instance=RequestContext(request))



def browse(request):

    presenter = request.GET.get('presenter')
    tags = request.GET.getlist('tag') + filter(None, request.GET.get('t', '').split('||'))
    remove_tag = request.GET.get('rt')
    if remove_tag and remove_tag in tags:
        tags.remove(remove_tag)
    keywords = request.GET.get('kw', '')
    querystring = request.GET.urlencode()

    if request.user.is_authenticated():
        existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))
    else:
        existing_tags = ()

    if tags:
        qs = OwnedWrapper.objects.filter(content_type=OwnedWrapper.t(Presentation))
        ids = list(TaggedItem.objects.get_by_model(qs, tags).values_list('object_id', flat=True))
        q = Q(id__in=ids)
    else:
        q = Q()
        
    if presenter:
        presenter = User.objects.get(username=presenter)
        qp = Q(owner=presenter)
    else:
        qp = Q()
        
    if keywords:
        qk = Q(*(Q(title__icontains=kw) | Q(description__icontains=kw) |
                 Q(owner__last_name__icontains=kw) | Q(owner__first_name__icontains=kw) |
                 Q(owner__username__icontains=kw) for kw in keywords.split()))
    else:
        qk = Q()
        
    presentations = Presentation.objects.select_related('owner').filter(q, qp, qk, id__in=accessible_ids(request.user, Presentation)).order_by('title')

    class ManagePresentationsForm(forms.Form):
       tags = SplitTaggingField(label='Existing Tags',
                                choices=[(t, t) for t in existing_tags],
                                required=False,
                                add_label='Additional tags')
       mode = forms.ChoiceField(label='Action',
                                required=True,
                                choices=[('add', 'Add to existing tags'),
                                         ('replace', 'Replace existing tags'),
                                         ('remove', 'Remove existing tags')],
                                initial='add',
                                widget=forms.RadioSelect)

    if request.method == "POST":
        ids = map(int, request.POST.getlist('h'))
        form = ManagePresentationsForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['mode']
            for presentation in presentations.filter(id__in=ids):
                if action == 'replace':
                    Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                            form.cleaned_data['tags'])
                elif action == 'add':
                    for tag in parse_tag_input(form.cleaned_data['tags']):
                        Tag.objects.add_tag(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                            '"%s"' % tag)
                elif action == 'remove':
                    Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation), '')                    
            return HttpResponseRedirect(reverse('presentation-browse') + '?' + querystring)
    else:
        form = ManagePresentationsForm()



    active_tags = tags
    active_presenter = presenter

    def col(model, field):
        qn = backend.DatabaseOperations().quote_name
        return '%s.%s' % (qn(model._meta.db_table), qn(model._meta.get_field(field).column))

    q = OwnedWrapper.objects.extra(
        tables=(Presentation._meta.db_table,),
        where=('%s=%s' % (col(OwnedWrapper, 'object_id'), col(Presentation, 'id')),
               '%s=%s' % (col(OwnedWrapper, 'user'), col(Presentation, 'owner')))).filter(
        object_id__in=presentations.values('id'),
        content_type=OwnedWrapper.t(Presentation))

    tags = Tag.objects.usage_for_queryset(q, counts=True)
    
    if request.user.is_authenticated():
        usertags = Tag.objects.usage_for_queryset(OwnedWrapper.objects.filter(
                        user=request.user,
                        object_id__in=presentations.values('id'),
                        content_type=OwnedWrapper.t(Presentation)), counts=True)
    else:
        usertags = ()
    
    presenters = User.objects.filter(presentation__in=presentations) \
                     .annotate(presentations=Count('presentation')).order_by('last_name', 'first_name')

    return render_to_response('presentation_browse.html',
                          {'tags': tags if len(tags) > 0 else None,
                           'usertags': usertags if len(usertags) > 0 else None,
                           'active_tags': active_tags,
                           'active_presenter': presenter,
                           'presentations': presentations,
                           'presenters': presenters if len(presenters) > 1 else None,
                           'keywords': keywords,
                           'querystring': querystring,
                           'form': form,
                           },
                          context_instance=RequestContext(request))

    pass
