from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue

def get_collection():
	collection, created = Collection.objects.get_or_create(
		name='unitedsearch',
		defaults={
			'title': 'United Search collection',
			'hidden': True,
			'description': 'Collection for images retrieved through the United Search'
		})
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=collection, usergroup=authenticated_users, read=True)
	return collection

def get_storage():
	storage, created = Storage.objects.get_or_create(
		name='unitedsearch',
		defaults={
			'title': 'United Search collection',
			'system': 'local',
			'base': os.path.join(settings.AUTO_STORAGE_DIR, 'unitedsearch')
		})
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=storage, usergroup=authenticated_users, read=True)
	return storage
