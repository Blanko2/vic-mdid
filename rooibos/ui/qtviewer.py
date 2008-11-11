from viewers import register_inlineviewer

def qt_inlineviewer(media):
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
</script>
    """ % (url)

register_inlineviewer(qt_inlineviewer)
