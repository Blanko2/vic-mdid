from django.core.management.base import BaseCommand
from rooibos.storage.models import Media

class Command(BaseCommand):
    help = 'Manages media metadata\nAvailable commands: refresh'
    args = 'command'

    def handle(self, *commands, **options):
        if not commands:
            print self.help
        else:
            for command in commands:
                if command == 'refresh':
                    self.refresh()
                else:
                    print "Invalid command %s" % command
    
    def refresh(self):
        count = 0
        allmedia = Media.objects.all()
        total = len(allmedia)
        for media in allmedia:
            media.identify()
            count += 1
            print "%s/%s\r" % (count, total),
        print
