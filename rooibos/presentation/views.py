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
        tags = forms.MultipleChoiceField(label='File under', choices=((t, t) for t in existing_tags),
                                         required=False)
        new_tags = TagField(label='File under', max_length=255, required=False)
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
            
            tags = form.cleaned_data['tags'] + parse_tag_input(form.cleaned_data['new_tags'])
            Tag.objects.update_tags(OwnedWrapper.objects.get_for_object(user=request.user, object=presentation),
                                    '"%s"' % '","'.join(tags))
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
    pass
