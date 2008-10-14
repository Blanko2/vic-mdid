from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from xml.dom import minidom
import os
import pyodbc
from rooibos.data.models import Group, NAME_MAX_LENGTH

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
        
        self.migrateCollections(cursor)
        
        
    def migrateCollections(self, cursor):
        
        groups = {}
        collgroups = {}

        for row in cursor.execute("SELECT ID,Title FROM CollectionGroups"):
            collgroups[row.ID] = Group.objects.create(title=row.Title)

        for row in cursor.execute("SELECT ID,Title,Description,UsageAgreement,GroupID FROM Collections"):
            groups[row.ID] = Group.objects.create(title=row.Title, description=row.Description, agreement=row.UsageAgreement)            
            if collgroups.has_key(row.GroupID):
                collgroups[row.GroupID].subgroups.add(groups[row.ID])

    