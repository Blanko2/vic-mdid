from django import template
from django.template.loader import render_to_string
from impersonate.functions import get_real_user, get_available_users
from django.template import RequestContext

register = template.Library()


class ImpersonationFormNode(template.Node):
    def render(self, context):
        request = context['request']
        current = get_real_user(request)
        users = get_available_users(current or request.user.username).count()
        if users:
            return render_to_string('impersonation_form.html',
                                    {'users': users,
                                     'current': current,
                                     'request': request,},
                                    context_instance=RequestContext(request))
        else:
            return ''


@register.tag
def impersonation_form(parser, token):
    return ImpersonationFormNode()
