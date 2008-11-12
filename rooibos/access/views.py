from django.db.models import Q
from django.http import Http404
from models import AccessControl

def get_effective_permissions(user, model_instance):
    if user.is_superuser:
        return (True, True, True)
    
    field = model_instance._meta.object_name.lower()

    if user.is_anonymous():
        q = Q(user=None, usergroup=None)
    else:
        q = Q(user=user) | Q(usergroup__in=user.groups.all())
    aclist = AccessControl.objects.filter(q, **{field: model_instance})
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


def filter_by_access(user, queryset, read=True, write=False, manage=False):
    if not (read or write or manage) or user.is_superuser:  # nothing to do
        return queryset
    model_id = queryset.model._meta.object_name.lower() + '_id'
    usergroups_q = Q(usergroup__in=user.groups.all().values('id').query)
    user_q = user.is_anonymous() and Q(user__isnull=True, usergroup__isnull=True) or Q(user=user)

    def build_query(**kwargs):
        (field, check) = kwargs.popitem()
        if not check:
            return Q()
        group_allowed_q = Q(id__in=AccessControl.objects.filter(usergroups_q, **{field: True}).values(model_id).query)
        group_denied_q = Q(id__in=AccessControl.objects.filter(usergroups_q, **{field: False}).values(model_id).query)
        user_allowed_q = Q(id__in=AccessControl.objects.filter(user_q, **{field: True}).values(model_id).query)
        user_denied_q = Q(id__in=AccessControl.objects.filter(user_q, **{field: False}).values(model_id).query)
        return ((group_allowed_q & ~group_denied_q) | user_allowed_q) & ~user_denied_q
        
    return queryset.filter(build_query(read=read), build_query(write=write), build_query(manage=manage)).distinct()
