from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from xml.dom import minidom
import os
import pyodbc
from datetime import datetime
from rooibos.data.models import Group, Field, FieldValue, Record

class Command(BaseCommand):
    help = 'Migrates database from older version'
    args = "config_file"

    def readConfig(self, file):
        connection = None
        servertype = None        
        config = minidom.parse(file)
        for e in config.getElementsByTagName('database')[0].childNodes:
            if e.localName == 'connection':
                connection = e.firstChild.nodeValue
            elif e.localName == 'servertype':
                servertype = e.firstChild.nodeValue
        return (servertype, connection)

    def clearDatabase(self):
        FieldValue.objects.all().delete()
        Field.objects.all().delete()
        Record.objects.all().delete()
        Group.objects.all().delete()

    def handle(self, *config_files, **options):
        if len(config_files) != 1:
            print "Please specify exactly one configuration file."
            return
        
        servertype, connection = self.readConfig(config_files[0])
        
        conn = None
        if servertype == "MSSQL":
            conn = pyodbc.connect('DRIVER={SQL Server};%s' % connection)
        elif servertype == "MYSQL":
            conn = pyodbc.connect('DRIVER={MySQL};%s' % connection)
        else:
            print "Unsupported database type"
            return
        
        cursor = conn.cursor()
        row = cursor.execute("SELECT Version FROM DatabaseVersion").fetchone()
        version = row.Version
        
        if version != "00008":
            print "Database version is not supported"
            return
        
        print "Migrating from version %s" % version
        
        print "Clearing database"
        self.clearDatabase()
        
        # Migrate collections and collection groups
         
        print "Migrating collections"
        groups = {}
        collgroups = {}

        for row in cursor.execute("SELECT ID,Title FROM CollectionGroups"):
            collgroups[row.ID] = Group.objects.create(title=row.Title)

        for row in cursor.execute("SELECT ID,Title,Description,UsageAgreement,GroupID FROM Collections"):
            groups[row.ID] = Group.objects.create(title=row.Title, description=row.Description, agreement=row.UsageAgreement)            
            if collgroups.has_key(row.GroupID):
                collgroups[row.GroupID].subgroups.add(groups[row.ID])

        # Migrate fields
        
        print "Migrating fields"
        fields = {}
        
        for row in cursor.execute("SELECT ID,Name FROM FieldDefinitions"):
            fields[row.ID] = Field.objects.create(label=row.Name)
        
        # Migrate records
        
        print "Migrating records"
        images = {}
        count = 0
        
        for row in cursor.execute("SELECT ID,CollectionID,Created,Modified,RemoteID," +
                                  "CachedUntil,Expires,UserID,Flags FROM Images"):
            images[row.ID] = Record.objects.create(created=row.Created or row.Modified or datetime.now(),
                                                   modified=row.Modified or datetime.now(),
                                                   source=row.RemoteID,
                                                   next_update=row.CachedUntil or row.Expires)
            groups[row.CollectionID].records.add(images[row.ID])
            count += 1
            if count % 100 == 0:
                print "%s\r" % count,

        # Migrate field values
        
        print "Migrating field values"
        count = 0
        
        for row in cursor.execute("SELECT ImageID,FieldID,FieldValue,OriginalValue,Type,Label " +
                                  "FROM FieldData INNER JOIN FieldDefinitions ON FieldID=FieldDefinitions.ID"):            
            FieldValue.objects.create(record=images[row.ImageID],
                                      field=fields[row.FieldID],
                                      label=row.Label,
                                      value=row.FieldValue,
                                      type=row.Type == 2 and 'D' or 'T')
            count += 1
            if count % 100 == 0:
                print "%s\r" % count,
                