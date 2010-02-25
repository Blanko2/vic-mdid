from django.http import HttpResponse, Http404,  HttpResponseRedirect, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from models import JobInfo

@login_required
def joblist(request):
    
    if request.user.is_superuser:
        jobs = JobInfo.objects.all()
    else:
        jobs = JobInfo.objects.filter(owner=request.user)
    
    if request.method == "POST":
        ids = request.POST.getlist('r')
        jobs.filter(id__in=ids, completed=True).delete()
        return HttpResponseRedirect(reverse('workers-jobs'))
    
    return render_to_response("workers_jobs.html",
                              {'jobs': jobs,
                               'owner': request.user if not request.user.is_superuser else None,
                               },
                              context_instance=RequestContext(request))