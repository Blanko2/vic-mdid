from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, get_list_or_404
from models import Media

def retrieve(request, record, media):
    mediaobj = get_object_or_404(Media, name=media, record__name=record)
    response = HttpResponse(content='', mimetype=mediaobj.mimetype)
    return response

def thumbnail(request, record):
    media = get_list_or_404(Media, record__name=record)
    result = None
    
    # Find best media item for thumbnail use
    for m in media:
        # If media is named 'thumb', use it
        if m.name == 'thumb':
            result = m
            break
        # Any media is better than nothing
        if not result:
            result = m
            continue
        # Images are better than non-images
        if m.mimetype[:6] == 'image/':
            if result.mimetype[:6] != 'image/':
                result = m
                continue
            # JPEGs are better than other images
            if m.mimetype == 'image/jpeg':
                if result.mimetype != 'image/jpeg':
                    result = m
                    continue                
                # Find something as close to 100x100 as possible
                try:  # In case height or width is not available
                    if m.height <= 100 and m.width <= 100 and (result.height > 100 or result.width > 100 or (m.height * m.width > result.height * result.width)):
                        result = m
                        continue
                except TypeError:
                    pass

    # conversion to 100x100 JPEG if necessary
    
    # could not find media or conversion to image impossible
    if not result:
        raise Http404
    
    # return result
    response = HttpResponse(content=result.load_file(), mimetype=str(result.mimetype))
    return response
