from __future__ import with_statement
import Image
import StringIO
from django.conf import settings
from django.db import connection
from django.db.models import Q, F
from rooibos.access import accessible_ids, get_effective_permissions_and_restrictions
from rooibos.data.models import Collection
from rooibos.presentation.models import Presentation
from models import Media, Storage

# sort images by area
def _imgsizecmp(x, y):
    if x.width and x.height and y.width and y.height:
        return cmp(x.width * x.height, y.width * y.height)
    if x.width and x.height:
        return 1
    if y.width and y.height:
        return -1
    return 0


def get_media_for_record(record, user=None, passwords={}):
    """
    Returns all media accessible to the user either directly through collections
    or indirectly through presentations.
    A user always must have access to the storage where the media is stored.
    """
    
    if hasattr(record, 'id'):
        recordid = record.id
    else:
        recordid = record

    # get available media objects
    # Has access to collection containing record and to storage containing media
    media = Media.objects.filter(        
        Q(record__collection__id__in=accessible_ids(user, Collection)) # record is accessible
        | Q(   # or presentation containing the record is accessible
            Q(record__presentationitem__presentation__password=None) |
            Q(record__presentationitem__presentation__in=Presentation.check_passwords(passwords)),
            record__presentationitem__presentation__id__in=accessible_ids(user, Presentation)
        ),
        storage__id__in=accessible_ids(user, Storage),  # storage always must be accessible
        record__id=recordid
    )

    return media


def get_image_for_record(record, user=None, width=100000, height=100000, passwords={}):
    
    media = get_media_for_record(record, user, passwords)

    media = media.filter(                          
        master=None,  # don't look for derivatives here
        mimetype__startswith='image/'
    )
    
    if not media:
        return None

    map(lambda m: m.identify(), (m for m in media if not m.width or not m.height))
   
    media = sorted(media, _imgsizecmp, reverse=True)
    
    # find matching media
    last = None
    for m in media:
        if m.width > width or m.height > height:
            # Image still larger than given dimensions
            last = m
        elif (m.width == width and m.height <= height) or (m.width <= width and m.height == height):
            # exact match
            break
        else:
            # Now we have a smaller image
            m = last or m
            break

    # m is now equal or larger to requested size
    
    # check what user size restrictions are
    restrictions = get_effective_permissions_and_restrictions(user, m.storage)[3]
    if restrictions:
        width = min(width, restrictions.get('width', width))
        height = min(height, restrictions.get('height', height))

    # see if image needs resizing  
    if m.width > width or m.height > height or m.mimetype != 'image/jpeg':
        
        def derivative_image(master, width, height):
            file = None
            try:
                file = master.load_file()
                image = Image.open(file)
                image.thumbnail((width, height), Image.ANTIALIAS)
                output = StringIO.StringIO()
                image.save(output, 'JPEG', quality=95, optimize=True)
                return output, image.size
            finally:
                if file:
                    file.close()
                
        # See if a derivative already exists
        d = m.derivatives.filter(Q(width=width, height__lte=height) | Q(width__lte=width, height=height),
                                 mimetype='image/jpeg')
        if d:
            # use derivative            
            d = d[0]
            if not d.file_exists():
                # file has been removed, recreate
                output, (w, h) = derivative_image(m, width, height)
                d.save_file('%s-%sx%s.jpg' % (d.id, w, h), output)            
            m = d
        else:
            # create new derivative with correct size
            output, (w, h) = derivative_image(m, width, height)
            storage = m.storage.get_derivative_storage()
            m = Media.objects.create(record=m.record, storage=storage, mimetype='image/jpeg',
                                     width=w, height=h, master=m)
            m.save_file('%s-%sx%s.jpg' % (m.id, w, h), output)

    return m



def get_thumbnail_for_record(record, user=None):
    return get_image_for_record(record, user, width=100, height=100)
