from viewers import register_inlineviewer

def jpeg_inlineviewer(media):
    if media.mimetype != 'image/jpeg':
        return None
    
    if media.width and media.width <= 800 and media.height and media.height <= 800:
        return "<img src='%s' />" % media.get_absolute_url()
        
    return None

register_inlineviewer(jpeg_inlineviewer)
