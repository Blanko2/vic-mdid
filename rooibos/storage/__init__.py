from models import Media
from rooibos.util import cached_property


# sort images by area
def _imgsizecmp(x, y):
    if x.width and x.height and y.width and y.height:
        return cmp(x.width * x.height, y.width * y.height)
    if x.width and x.height:
        return 1
    if y.width and y.height:
        return -1
    return 0
    

def get_image_for_record(record, width, height, prefer_larger=False):    
    media = sorted(Media.objects.filter(record=record, mimetype__startswith='image/'), _imgsizecmp, reverse=True)
    if not media:
        return None
    
    last = None
    for m in media:
        if m.width > width or m.height > height:
            # Image still larger than given dimensions
            last = m
        else:
            # Now we have a smaller image
            if prefer_larger:
                # We want one that is bigger, if available
                return last or m
            else:
                return m
    # did not find any, return last one as it should be closest to what we want
    return m


def get_thumbnail_for_record(record):
    
    def query():
        return get_image_for_record(record, 100, 100)

    return cached_property(record, 'thumbnail', query)
