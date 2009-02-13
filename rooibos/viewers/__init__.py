viewers = {}


def register_viewer(viewer):
    for type in viewer.types:
        for target in viewer.targets:
            viewers.setdefault(type, {}).setdefault(target, []).insert(0, viewer)

    
def generate_view_inline(object):
    for iv in viewers.setdefault(object._meta.object_name.lower(), {}).setdefault('inline', []):
        result = iv().generate(object)
        if result:
            return result
    return None


def get_viewers(type, target):
    return list(viewers.setdefault(type, {}).setdefault(target, []))


class DefaultMediaViewInline:
    title = "Default inline media viewer"    
    types = ('media',)
    targets = ('inline',)
    
    def generate(self, object):
        return "[%s]" % media.mimetype


class DefaultGroupViewInline:
    title = "Default inline collection viewer"
    types = ('collection',)
    targets = ('inline',)
    
    def generate(self, object):
        return "[%s]" % object.title


class JpegMediaViewInline:
    title = "JPEG inline media viewer"    
    types = ('media',)
    targets = ('inline',)
    
    def generate(self, object):    
        if object.mimetype != 'image/jpeg':
            return None
        return "<div style='max-width: 900px; max-height: 600px; overflow: auto;'><img src='%s' /></div>" % \
            object.get_absolute_url()


class QuickTimeMediaViewInline:
    title = "JPEG inline media viewer"    
    types = ('media',)
    targets = ('inline',)
    
    def generate(self, object):    
        if media.mimetype != 'video/quicktime':
            return None
        
        url = media.get_absolute_url()
        if url.startswith('http'):
            return '<a href="%s">%s</a>' % (url, 'Download Quicktime Video')
        else:
            return """
<script src='/static/viewers/qtviewer/AC_QuickTime.js' language='JavaScript' type='text/javascript'></script>
<script language='JavaScript' type='text/javascript'>
QT_WriteOBJECT('/static/viewers/qtviewer/watchnow.mov','91','15','',
'controller','false',
'autoplay','true',
'loop','false',
'cache','true',
'href','%s',
'target','quicktimeplayer',
'align','absmiddle',
'vspace','5',
'style','margin-top: 5px; margin-bottom: 5px'
);	
</script>""" % (url)


register_viewer(DefaultMediaViewInline)
register_viewer(DefaultGroupViewInline)
register_viewer(QuickTimeMediaViewInline)
register_viewer(JpegMediaViewInline)

