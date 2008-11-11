from django.db.models import Q
from django.http import Http404
from models import AccessControl

def get_effective_permissions(user, model_instance):
    if user.is_superuser:
        return (True, True, True)
    
    field = model_instance._meta.object_name.lower()

    aclist = AccessControl.objects.filter(Q(user=user) | Q(usergroup__in=user.groups.all()), **{field: model_instance})
    def reduce_by_filter(f):
        def combine(a, b):
            if a == False or (a == True and b == None):
                return a
            else:
                return b
        read = write = manage = None
        for ac in filter(f, aclist):
            read = combine(ac.read, read)
            write = combine(ac.write, write)
            manage = combine(ac.manage, manage)
        return (read, write, manage)
    
    (gr, gw, gm) = reduce_by_filter(lambda a: a.usergroup)
    (ur, uw, um) = reduce_by_filter(lambda a: a.user)
    
    return (ur or (ur == None and gr),
            uw or (uw == None and gw),
            um or (um == None and gm))


def check_access(user, model_instance, read=True, write=False, manage=False, fail_if_denied=False):
    (r, w, m) = get_effective_permissions(user, model_instance)
    if (read and not r) or (write and not w) or (manage and not m):
        if fail_if_denied:
            raise Http404
        return False
    return True
