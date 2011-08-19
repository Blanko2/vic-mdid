from optparse import make_option, OptionValueError
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import connection
from django.contrib.contenttypes.models import ContentType
from dateutil.parser import parse as parse_date
from rooibos.data.models import Collection, Record, CollectionItem, standardfield_ids, FieldValue
from rooibos.storage.models import Media
from rooibos.statistics.models import AccumulatedActivity, Activity
from rooibos.statistics.functions import accumulate, assure_accumulation
import csv
import datetime
import sys


def _validate_date(option, opt_str, value, parser):
    try:
        setattr(parser.values, option.dest, parse_date(value))
    except (ValueError, AttributeError):
        raise OptionValueError("Invalid date specified for %s" % opt_str)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--collection', '-c', dest='collection', help='Target collection'),
        make_option('--start', '-s', dest='from_date', type='string', action='callback',
                    callback=_validate_date, help='Start date (inclusive)'),
        make_option('--end', '-e', dest='until_date', type='string', action='callback',
                    callback=_validate_date, help='End date (exclusive)'),
        make_option('--format', '-f', dest='file_format', type='choice',
                    choices=['csv'], default='csv', help='File format'),
        make_option('--output', '-o', dest='file_name', type='string',
                    help='File format'),
        make_option('--include', '-i', dest='include_events', action='append',
                    default=[], help='Include specified event'),
        make_option('--exclude', '-x', dest='exclude_events', action='append',
                    default=[], help='Exclude specified event'),
        make_option('--list', '-l', dest='list_events', action='store_true',
                    help='List effective events and exit'),
    )
    help = "Exports statistics for a specified collection and time range"


    def handle(self, collection, from_date, until_date, file_format, file_name,
               include_events, exclude_events, list_events, *args, **options):

        events = list(Activity.objects.distinct()
                      .order_by('event').values_list('event', flat=True))

        if include_events:
            events = include_events
        for event in exclude_events:
            if event in events:
                events.remove(event)

        if list_events:
            print "Events (not all may apply to date range or collection):"
            print '\n'.join(events)
            return

        if not from_date:
            print "Please specify a start date"
            return
        if not collection:
            print "Please specify a collection"
            return

        try:
            collection = Collection.objects.get(name=collection)
        except Collection.DoesNotExist:
            try:
                collection = Collection.objects.get(id=collection)
            except (Collection.DoesNotExist, ValueError):
                print "Cannot find specified collection: %s" % collection
                return

        def accumulation_status(date, event, step, numsteps):
            print >> sys.stderr, "Accumulating data for event %s on %s... (%d/%d)" % (
                event, date, step + 1, numsteps)
        assure_accumulation(from_date, until_date, events, callback=accumulation_status)

        activity = AccumulatedActivity.objects.filter(object_id__isnull=False, date__gte=from_date)
        if until_date:
            activity = activity.filter(date__lt=until_date)

        record_ids = CollectionItem.objects.filter(collection=collection, record__owner__isnull=True).values('record')
        media = Media.objects.filter(record__in=record_ids).select_related('storage')
        media_dict = dict((id, (record, name))
                           for id, record, name in media.values_list('id', 'record', 'storage__name'))

        record_type = ContentType.objects.get_for_model(Record)
        media_type = ContentType.objects.get_for_model(Media)

        activity = activity.filter(
            (Q(content_type=record_type, object_id__in=record_ids) |
             Q(content_type=media_type, object_id__in=media.values('id')))
            )

        records = dict()
        identifier_field = standardfield_ids('identifier', equiv=True)
        title_field = standardfield_ids('title', equiv=True)

        if file_name:
            output = open(file_name, 'wb')
        else:
            output = sys.stdout

        writer = csv.writer(output, dialect='excel')
        writer.writerow((
            'Date',
            '',
            'Record',
            'Title',
            'Media',
            'Storage',
            'Event',
            'Count',
        ))

        for entry in activity.select_related('content_type').order_by('date', 'event'):
            if entry.content_type == media_type:
                record_id, storage = media_dict[entry.object_id]
                media_id = entry.object_id
            else:
                record_id = entry.object_id
                media_id = None
                storage = None

            if records.has_key(record_id):
                identifier, title = records[record_id]
            else:
                try:
                    identifier = FieldValue.objects.filter(record=record_id,
                                                           field__in=identifier_field,
                                                           ).order_by('order')[0].value
                    identifier = identifier.encode('utf-8')
                except Exception, e:
                    print >> sys.stderr, e
                    identifier = None
                try:
                    title = FieldValue.objects.filter(record=record_id,
                                                           field__in=title_field,
                                                           ).order_by('order')[0].value
                    title = title.encode('utf-8')
                except Exception, e:
                    print >> sys.stderr, e
                    title = None

                records[record_id] = (identifier, title)

            writer.writerow((
                str(entry.date),
                record_id,
                identifier,
                title,
                media_id,
                storage,
                entry.event,
                entry.count,
            ))


        if file_name:
            output.close()

        print >> sys.stderr, '%d queries' % len(connection.queries)
