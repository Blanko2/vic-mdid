from django.core.exceptions import MiddlewareNotUsed
import logging
from models import Storage, Media

class StorageCleanupOnStart:

    def __init__(self):

        try:
        #Derivative storage no longer used, remove all from database
        #Due to dependencies, need to delete them individually after removing the derivative connections
            storage_ids = list(Media.objects.filter(master__isnull=False).values_list('storage__id', flat=True).distinct())
            storage_ids.extend(Storage.objects.exclude(id__in=Media.objects.all().values('storage__id'))
                                              .filter(base__startswith='d:/mdid/scratch/').values_list('id', flat=True))
            for storage in Storage.objects.filter(master__isnull=False).exclude(id__in=storage_ids):
                storage_ids.append(storage.id)
            for storage in Storage.objects.filter(id__in=storage_ids):
                try:
                    storage.master.derivative = None
                    storage.master.save()
                except Storage.DoesNotExist:
                    pass
            for storage in Storage.objects.filter(id__in=storage_ids):
                storage.delete()
            logging.info("Derivative storage cleanup completed")
        except Exception, ex:
            # Clean up failed, log exception and continue
            logging.error("Derivative storage cleanup failed: %s" % ex)
            pass

        raise MiddlewareNotUsed
