from functions import register_viewer, Viewer, get_viewers_for_object




#from inspect import getmembers, isclass
#from django.conf.urls.defaults import url
#
#viewer_classes = []
#
FULL_SUPPORT = 1
PARTIAL_SUPPORT = 2
NO_SUPPORT = 0
#
#
#def viewer(viewer_class):
#    """
#    Add an instance of the viewer class to the list of available viewer classes
#    """
#
#    # discard name
#    viewer_class = viewer_class[1]
#
#    v = viewer_class()
#    if hasattr(v, 'analyze'):
#        global viewer_classes
#        viewer_classes.append(v)
#
#
#def get_viewers_for_object(obj, user, inline=False):
#    vcs = inline and filter(lambda v: hasattr(v, 'inline'), viewer_classes) or viewer_classes
#    return filter(lambda v: v.analyze(obj, user) != NO_SUPPORT, vcs)
#
#
#def get_viewer_urls():
#    result = []
#    for v in filter(lambda v: hasattr(v, 'url'), viewer_classes):
#        urls = v.url()
#        if hasattr(urls, '__iter__'):
#            result = result + urls
#        else:
#            result.append(urls)
#    return result
#
#
#import viewers
#map(viewer, getmembers(viewers, isclass))
#
