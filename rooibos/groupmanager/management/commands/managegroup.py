from optparse import make_option
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from rooibos.storage.models import Storage
from rooibos.data.models import Collection
from rooibos.access.models import AccessControl, ContentType


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--name', '-n', dest='usergroup',
                    help='Name of user group to be managed'),
        make_option('--storage', '-s', dest='storagepath',
                    help='Create storage at specified path'),
        make_option('--storageurlbase', dest='storageurlbase',
                    help='Storage URL base'),
        make_option('--storageserverbase', dest='storageserverbase',
                    help='Storage server base'),
        make_option('--collection', '-c', dest='createcollection',
                    action='store_true', help='Create collection'),
        make_option('--collectiongroup', '-g', dest='collectiongroup',
                    help='Name of optional collection group'),
        make_option('--users', '-u', dest='users',
                    help='Comma-separated list of usernames for group ' +
                    '(removes all others)'),
        make_option('--adduser', '-a', dest='adduser', action='append',
                    help='Add user to group (repeat for multiple users)'),
        make_option('--removeuser', '-r', dest='removeuser', action='append',
                    help='Remove user from group (repeat for multiple users)'),
    )
    help = "Creates groups, manages memberships and optionally creates " + \
           "associated storage and collection"


    def handle(self, usergroup, storagepath, storageurlbase,
               storageserverbase, createcollection, collectiongroup,
               users, adduser, removeuser, *args, **kwargs):

        def message(msg):
            if kwargs.has_key('output'):
                kwargs['output'].append(msg)
            else:
                print msg


        if not usergroup:
            message("--name is a required parameter.")
            return

        group, created = Group.objects.get_or_create(name=usergroup)


        def process_users(users, action):
            for username in users:
                try:
                    action(User.objects.get(username=username))
                except User.DoesNotExist:
                    message("User '%s' not found, ignored." % username)

        if users:
            group.user_set.clear()
            process_users(users.split(','), group.user_set.add)
        if adduser:
            process_users(adduser, group.user_set.add)
        if removeuser:
            process_users(removeuser, group.user_set.remove)


        if createcollection:
            collection, created = Collection.objects.get_or_create(
                title=usergroup,
            )
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Collection),
                object_id=collection.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                    write=True,
                )
            )
        else:
            collection = None

        if collectiongroup:
            parent_collection, created = Collection.objects.get_or_create(
                title=collectiongroup,
            )
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Collection),
                object_id=parent_collection.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                )
            )
            if collection:
                parent_collection.children.add(collection)

        if storagepath:
            storage, created = Storage.objects.get_or_create(
                title=usergroup,
                defaults=dict(
                    system='local',
                    base=storagepath,
                    urlbase=storageurlbase,
                    deliverybase=storageserverbase,
                )
            )
            AccessControl.objects.get_or_create(
                content_type=ContentType.objects.get_for_model(Storage),
                object_id=storage.id,
                usergroup=group,
                defaults=dict(
                    read=True,
                    write=True,
                )
            )
