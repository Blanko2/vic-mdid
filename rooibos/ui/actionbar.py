from rooibos.contrib.tagging.models import Tag, TaggedItem
from rooibos.contrib.tagging.forms import TagField
from rooibos.contrib.tagging.utils import parse_tag_input
from rooibos.util.models import OwnedWrapper
import base64


def update_actionbar_tags(request, *objects):

    # split tags on commas unless there is a quote in the input
    nt = request.POST.get('new_tags')
    if '"' in nt:
        new_tags = parse_tag_input(nt)
    else:
        new_tags = filter(None, map(lambda s: s.strip(), nt.split(',')))
    all_tags = parse_tag_input(request.POST.get('all_tags'))
    try:
        update_tags = dict((base64.b32decode(k[11:].replace('_', '=')), v)
            for k, v in request.POST.iteritems()
            if k.startswith('update_tag_'))
    except TypeError:
        # Could not decode base32 encoded tag names
        update_tags = ()

    remove_tags = [tag_name for tag_name in all_tags
                   if tag_name not in update_tags.keys() and tag_name not in new_tags]

    for obj in objects:
        wrapper = OwnedWrapper.objects.get_for_object(user=request.user, object=obj)
        for tag_name, action in update_tags.iteritems():
            if action == 'mixed':
                # Don't need to change anything
                continue
            elif action == 'true':
                # Add tag to all selected presentations
                Tag.objects.add_tag(wrapper, '"%s"' % tag_name)
        for tag_name in new_tags:
            Tag.objects.add_tag(wrapper, '"%s"' % tag_name)
        for tag_name in remove_tags:
            keep_tags = Tag.objects.get_for_object(wrapper).exclude(name=tag_name).values_list('name')
            Tag.objects.update_tags(wrapper,  ' '.join(map(lambda s: '"%s"' % s, keep_tags)))
