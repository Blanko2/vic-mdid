inlineviewers = []

def register_inlineviewer(viewer):
    inlineviewers.insert(0, viewer)
    
def generate_inlineviewer(media):
    for iv in inlineviewers:
        result = iv(media)
        if result:
            return result
    return None

def default_inlineviewer(media):
    return "[%s]" % media.mimetype

register_inlineviewer(default_inlineviewer)
