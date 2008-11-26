from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from rooibos.data.models import Group, Record
from rooibos.storage.models import Media
from rooibos.util import get_full_url

class GroupFeed(Feed):

    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Group.objects.get(name=bits[0])
    
    def title(self, group):
        return group.title
    
    def link(self, group):
        if not group:
            raise FeedDoesNotExist
        return group.get_absolute_url()
    
    def description(self, group):
        return group.description
    
    def items(self, group):
        return Record.objects.filter(group=group).order_by('groupmembership__order')

    thumbnails = {}

    def item_enclosure_url(self, record):
        media = self.thumbnails.setdefault(record, Media.get_thumbnail_for_record(record))
        return media and get_full_url(media.get_absolute_url()) or None
    
    def item_enclosure_mime_type(self, record):
        media = self.thumbnails.setdefault(record, Media.get_thumbnail_for_record(record))
        return media and media.mimetype or None

    def item_enclosure_length(self, record):
        return 0
    