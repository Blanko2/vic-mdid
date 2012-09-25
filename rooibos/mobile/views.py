from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_protect
from rooibos.userprofile.views import load_settings, store_settings
from rooibos.contrib.tagging.models import Tag
from rooibos.util.models import OwnedWrapper
from presentation.models import Presentation
from django.db.models import Q
from rooibos.access import filter_by_access
from django.db import backend
from django.contrib.auth.models import User
from django.db.models.aggregates import Count

from rooibos.unitedsearch import external
from urllib import urlencode

@csrf_protect
def m_main(request):
    print '** blah!!'
    form = AuthenticationForm()
    request.session.set_test_cookie()
    return render_to_response('m_main.html', {'form': form}, context_instance=RequestContext(request))

class usViewer():
    def __init__(self, searcher):
        self.searcher = searcher

    def search(self, request):
        query = request.GET.get('q', '') or request.POST.get('q', '')
        offset = int(request.GET.get('from', '') or request.POST.get('from', '') or 0)
        result = self.searcher.search(query, {}, offset, 6) # 50
        results = result.images
        return render_to_response('m_results.html',
            {
                'results': [ { 'thumb_url': i.thumb, 'title': i.name, 'record_url': i.infourl, 
                              'identifier': i.identifier } for i in results ],
                'next_page': reverse('mobile-search-results') + "?" + urlencode({ 'q': query, 'from': result.nextoffset }),
                'hits': result.total,
                'searcher_name': self.searcher.name
            },
            context_instance=RequestContext(request))
        
def m_search(request):
    viewer = usViewer(external.flickr)
    return viewer.search(request)

def m_browse(request, manage=False):
    if manage and not request.user.is_authenticated():
        raise Http404()

    if request.user.is_authenticated() and not request.GET.items():
        #retrieve past settings
        qs = load_settings(request.user, filter='presentation_browse_querystring')
        if qs.has_key('presentation_browse_querystring'):
            return HttpResponseRedirect('%s?%s' % (
                reverse('presentation-manage' if manage else 'presentation-browse'),
                qs['presentation_browse_querystring'][0],
                ))

    presenter = request.GET.get('presenter')
    tags = filter(None, request.GET.getlist('t'))
    untagged = 1 if request.GET.get('ut') else 0
    if untagged:
        tags = []
    remove_tag = request.GET.get('rt')
    if remove_tag and remove_tag in tags:
        tags.remove(remove_tag)
    keywords = request.GET.get('kw', '')
    get = request.GET.copy()
    get.setlist('t', tags)
    if get.has_key('rt'):
        del get['rt']
    if untagged:
        get['ut'] = '1'
    elif get.has_key('ut'):
        del get['ut']

    if request.user.is_authenticated():
        existing_tags = Tag.objects.usage_for_model(OwnedWrapper,
                        filters=dict(user=request.user, content_type=OwnedWrapper.t(Presentation)))
    else:
        existing_tags = ()


    if untagged and request.user.is_authenticated():
        qs = TaggedItem.objects.filter(content_type=OwnedWrapper.t(OwnedWrapper)).values('object_id').distinct()
        qs = OwnedWrapper.objects.filter(user=request.user, content_type=OwnedWrapper.t(Presentation), id__in=qs).values('object_id')
        q = ~Q(id__in=qs)
    elif tags:
        qs = OwnedWrapper.objects.filter(content_type=OwnedWrapper.t(Presentation))
        # get list of matching IDs for each individual tag, since tags may be attached by different owners
        ids = [list(TaggedItem.objects.get_by_model(qs, '"%s"' % tag).values_list('object_id', flat=True)) for tag in tags]
        q = Q(*(Q(id__in=x) for x in ids))
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

    if manage:
        qv = Q()
        presentations = filter_by_access(request.user, Presentation, write=True, manage=True)
    else:
        qv = Presentation.published_Q()
        presentations = filter_by_access(request.user, Presentation )

    presentations = presentations.select_related('owner').filter(q, qp, qk, qv).order_by('title')

    if request.method == "POST":

        if manage and (request.POST.get('hide') or request.POST.get('unhide')) and request.user.has_perm('presentation.publish_presentations'):
            hide = request.POST.get('hide') or False
            ids = map(int, request.POST.getlist('h'))
            for presentation in Presentation.objects.filter(owner=request.user, id__in=ids):
                presentation.hidden = hide
                presentation.save()

        if manage and request.POST.get('delete'):
            ids = map(int, request.POST.getlist('h'))
            Presentation.objects.filter(owner=request.user, id__in=ids).delete()

        get['kw'] = request.POST.get('kw')
        if get['kw'] != request.POST.get('okw') and get.has_key('page'):
            # user entered keywords, reset page counter
            del get['page']

        if request.POST.get('update_tags'):
            ids = map(int, request.POST.getlist('h'))
            update_actionbar_tags(request, *presentations.filter(id__in=ids))

        # check for clicks on "add selected items" buttons
        for button in filter(lambda k: k.startswith('add-selected-items-'), request.POST.keys()):
            id = int(button[len('add-selected-items-'):])
            presentation = get_object_or_404(
                filter_by_access(request.user, Presentation, write=True, manage=True).filter(id=id))
            add_selected_items(request, presentation)
            return HttpResponseRedirect(reverse('presentation-edit', args=(presentation.id, presentation.name)))

        return HttpResponseRedirect(request.path + '?' + get.urlencode())


    active_tags = tags
    active_presenter = presenter

    def col(model, field):
        qn = backend.DatabaseOperations().quote_name
        return '%s.%s' % (qn(model._meta.db_table), qn(model._meta.get_field(field).column))

    if presentations and not manage:
        q = OwnedWrapper.objects.extra(
            tables=(Presentation._meta.db_table,),
            where=('%s=%s' % (col(OwnedWrapper, 'object_id'), col(Presentation, 'id')),
                   '%s=%s' % (col(OwnedWrapper, 'user'), col(Presentation, 'owner')))).filter(
            object_id__in=presentations.values('id'),
            content_type=OwnedWrapper.t(Presentation))
        tags = Tag.objects.usage_for_queryset(q, counts=True)

        for p in presentations:
            p.verify_password(request)
    else:
        tags = ()

    if presentations and request.user.is_authenticated():
        usertags = Tag.objects.usage_for_queryset(OwnedWrapper.objects.filter(
                        user=request.user,
                        object_id__in=presentations.values('id'),
                        content_type=OwnedWrapper.t(Presentation)), counts=True)
    else:
        usertags = ()

    presenters = User.objects.filter(presentation__in=presentations) \
                     .annotate(presentations=Count('presentation')).order_by('last_name', 'first_name')

    if request.user.is_authenticated() and presentations:
        # save current settings
        querystring = request.GET.urlencode()
        store_settings(request.user, 'presentation_browse_querystring', querystring)

    return render_to_response('m_presentation_browse.html',
                          {'manage': manage,
                           'tags': tags if len(tags) > 0 else None,
                           'untagged': untagged,
                           'usertags': usertags if len(usertags) > 0 else None,
                           'active_tags': active_tags,
                           'active_presenter': presenter,
                           'presentations': presentations,
                           'presenters': presenters if len(presenters) > 1 else None,
                           'keywords': keywords,
                           },
                          context_instance=RequestContext(request))
        

