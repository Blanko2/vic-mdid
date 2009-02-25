from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required
from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.contrib.tagging.forms import TagField
from rooibos.contrib.tagging.utils import parse_tag_input
from django import forms
from models import Presentation, PresentationItem
from rooibos.util.models import OwnedWrapper
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from rooibos.access import filter_by_access, accessible_ids
from rooibos.ui.forms import SplitTaggingField


@login_required
def manage(request):

    tags = request.GET.getlist('tag')
    querystring = request.GET.urlencode()

    if request.method == "POST":
        ids = map(int, request.POST.getlist('h'))
        if request.POST.get('hide') or request.POST.get('unhide'):
            hide = request.POST.get('hide') or False
            for presentation in Presentation.objects.filter(owner=request.user, id__in=ids):
                presentation.hidden = hide
                presentation.save()
        return HttpResponseRedirect(reverse('presentation-manage') + '?' + querystring)

    if tags:
        qs = OwnedWrapper.objects.filter(user=request.user, type=OwnedWrapper.t(Presentation))
        ids = list(TaggedItem.objects.get_by_model(qs, tags).values_list('object_id', flat=True))
        presentations = Presentation.objects.filter(owner=request.user, id__in=ids).order_by('title')
    else:
        presentations = Presentation.objects.filter(owner=request.user).order_by('title')
    
    tag_filter = " and ".join(tags)
        
    tags = Tag.objects.cloud_for_model(OwnedWrapper, steps=5,
                        filters=dict(user=request.user, type=OwnedWrapper.t(Presentation)))
        
    return render_to_response('presentation_manage.html',
                          {'tags': tags,
                           'presentations': presentations,
                           'querystring': querystring,
                           'tag_filter': tag_filter,
                           },
                          context_instance=RequestContext(request))



@login_required
def create(request):

    existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, type=OwnedWrapper.t(Presentation)))

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
        OwnedWrapper, filters=dict(user=request.user, type=OwnedWrapper.t(Presentation)))]
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

