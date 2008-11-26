from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import _get_queryset

def get_effective_permissions(user, model_instance):
    from models import AccessControl
    if user.is_superuser:
        return (True, True, True)
    owner = getattr(model_instance, 'owner', None)
    if owner and owner == user:
        return (True, True, True)
    if user.is_anonymous():
        q = Q(user=None, usergroup=None)
    else:
        q = Q(user=user) | Q(usergroup__in=user.groups.all())
    model_type = ContentType.objects.get_for_model(model_instance)
    aclist = AccessControl.objects.filter(q, object_id=model_instance.id, content_type__pk=model_type.id)
    
    def reduce_by_filter(f):
        def combine(a, b):
            if a == False or (a == True and b == None): return a
            else: return b
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
            raise PermissionDenied
        return False
    return True


def filter_by_access(user, queryset, read=True, write=False, manage=False):
    from models import AccessControl
    queryset = _get_queryset(queryset)
    if not (read or write or manage) or user.is_superuser:  # nothing to do
        return queryset
    model_type = ContentType.objects.get_for_model(queryset.model)
    usergroups_q = Q(usergroup__in=user.groups.all().values('id').query)
    user_q = user.is_anonymous() and Q(user__isnull=True, usergroup__isnull=True) or Q(user=user)
    owner_q =  'owner' in (f.name for f in queryset.model._meta.fields) and Q(owner=user)

    def build_query(**kwargs):
        (field, check) = kwargs.popitem()
        if not check:
            return Q()
        user_allowed_q = Q(id__in=AccessControl.objects.filter(user_q, content_type__id=model_type.id,
                                                               **{field: True}).values('object_id').query)
        user_denied_q = Q(id__in=AccessControl.objects.filter(user_q, content_type__id=model_type.id,
                                                              **{field: False}).values('object_id').query)
        if user.is_anonymous():
            return user_allowed_q & ~user_denied_q
        group_allowed_q = Q(id__in=AccessControl.objects.filter(usergroups_q, content_type__id=model_type.id,
                                                                **{field: True}).values('object_id').query)
        group_denied_q = Q(id__in=AccessControl.objects.filter(usergroups_q, content_type__id=model_type.id,
                                                               **{field: False}).values('object_id').query)
        result = ((group_allowed_q & ~group_denied_q) | user_allowed_q) & ~user_denied_q
        if owner_q:
            result = owner_q | result
        return result
    
    return queryset.filter(build_query(read=read), build_query(write=write), build_query(manage=manage)).distinct()


def accessible_ids(user, queryset, read=True, write=False, manage=False):
    queryset = _get_queryset(queryset)
    return filter_by_access(user, queryset, read, write, manage).values('id').query


def accessible_ids_list(user, queryset, read=True, write=False, manage=False):
    queryset = _get_queryset(queryset)
    return filter_by_access(user, queryset, read, write, manage).values_list('id', flat=True)
