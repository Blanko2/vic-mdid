from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
from django.db import connection
from django.contrib.auth.models import User, Group as UserGroup
from xml.dom import minidom
import os
import pyodbc
from urlparse import urlparse
from datetime import datetime
from rooibos.data.models import Group, GroupMembership, Field, FieldValue, Record
from rooibos.storage.models import Storage, Media
from rooibos.solr.models import DisableSolrUpdates
from rooibos.solr import SolrIndex
from rooibos.access.models import AccessControl

IMPORT_COLLECTIONS = (15,)
IMPORT_RECORDS = 200

# old permissions

P = dict(
    _None = 0,
    ModifyACL = 1 << 0,
    CreateCollection = 1 << 1,
    ManageCollection = 1 << 2,
    DeleteCollection = 1 << 3,
    ModifyImages = 1 << 5,
    ReadCollection = 1 << 7,
    CreateSlideshow = 1 << 8,
    ModifySlideshow = 1 << 9,
    DeleteSlideshow = 1 << 10,
    ViewSlideshow = 1 << 11,
    CopySlideshow = 1 << 12,
    FullSizedImages = 1 << 13,
    AnnotateImages = 1 << 14,
    ManageUsers = 1 << 15,
    ImageViewerAccess = 1 << 16,
    PublishSlideshow = 1 << 17,
    ResetPassword = 1 << 18,
    ManageAnnouncements = 1 << 21,
    ManageControlledLists = 1 << 23,
    ManageCollectionGroups = 1 << 25,
    UserOptions = 1 << 26,
    PersonalImages = 1 << 27,
    ShareImages = 1 << 28,
    SuggestImages = 1 << 29,
    Unknown = 1 << 31,
)



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

        DisableSolrUpdates()        
   
        # Migrate users
        print "Migrating users"
        users = {}
        duplicate_login_check = {}
        for row in cursor.execute("SELECT ID,Login,Password,Name,FirstName,Email,Administrator,LastAuthenticated " +
                                  "FROM Users"):
            if duplicate_login_check.has_key(row.Login.lower()):
                print "Warning: duplicate login detected: %s" % row.Login
                continue
            users[row.ID] = user = User()
            user.username = row.Login[:30]
            duplicate_login_check[user.username] = None
            if row.Password:
                user.password = row.Password.lower()
            else:
                user.set_unusable_password()
            user.last_name = row.Name[:30]
            user.first_name = row.FirstName[:30]
            user.email = row.Email[:75]
            user.is_superuser = row.Administrator
            user.last_login = row.LastAuthenticated or datetime(1980, 1, 1)
            user.save()

        # Migrate user groups
        print "Migrating user groups"
        usergroups = {}
        for row in cursor.execute("SELECT ID,Title,Type FROM UserGroups"):
            usergroups[row.ID] = UserGroup.objects.create(name=row.Title)
            # todo: handle non-membership groups
        
        for row in cursor.execute("SELECT UserID,GroupID FROM UserGroupMembers"):
            if users.has_key(row.UserID):
                users[row.UserID].groups.add(usergroups[row.GroupID])
        
        # Migrate collections and collection groups
         
        print "Migrating collections"
        groups = {}
        collgroups = {}
        storage = {}

        for row in cursor.execute("SELECT ID,Title FROM CollectionGroups"):
            collgroups[row.ID] = Group.objects.create(title=row.Title, type='collection')

        for row in cursor.execute("SELECT ID,Type,Title,Description,UsageAgreement,GroupID,ResourcePath FROM Collections"):
            if row.ID in IMPORT_COLLECTIONS:
                manager = None
                if row.Type == 'N':
                    manager = 'nasaimageexchange'
                groups[row.ID] = Group.objects.create(title=row.Title, type='collection', description=row.Description, agreement=row.UsageAgreement)            
                if collgroups.has_key(row.GroupID):
                    collgroups[row.GroupID].subgroups.add(groups[row.ID])
                if row.Type in ('I', 'N', 'R'):
                    storage[row.ID] = Storage.objects.create(title=row.Title, system='local', base=row.ResourcePath.replace('\\', '/'))

        # Migrate collection permissions
       
        def populate_access_control(ac, row, readmask, writemask, managemask):
            def tristate(mask):
                if row.DenyPriv and row.DenyPriv & mask: return False
                if row.GrantPriv and row.GrantPriv & mask: return True                
                return None
            ac.read = tristate(readmask)
            ac.write = tristate(writemask)
            ac.manage = tristate(managemask)
            if row.UserID and users.has_key(row.UserID):
                ac.user = users[row.UserID]
            elif usergroups.has_key(row.GroupID):
                ac.usergroup = usergroups[row.GroupID]
            else:
                return False
            return True
       
        #Privilege.ModifyACL  -> manage
        #Privilege.ManageCollection  -> manage
        #Privilege.DeleteCollection  -> manage
        #Privilege.ModifyImages  -> write
        #Privilege.ReadCollection  -> read
        #Privilege.FullSizedImages  -> n/a
        #Privilege.AnnotateImages  -> n/a
        #Privilege.ManageControlledLists  -> manage
        #Privilege.PersonalImages  -> n/a
        #Privilege.ShareImages  -> n/a
        #Privilege.SuggestImages  -> n/a       
        
        for row in cursor.execute("SELECT ObjectID,UserID,GroupID,GrantPriv,DenyPriv " +
                                  "FROM AccessControl WHERE ObjectType='C' AND ObjectID>0"):
            if not groups.has_key(row.ObjectID):
                continue
            ac = AccessControl()
            ac.content_object = groups[row.ObjectID]            
            if populate_access_control(ac, row, P['ReadCollection'], P['ModifyImages'], P['ManageCollection']):
                ac.save()
            

        # Migrate fields
        
        print "Migrating fields"
        fields = {}
        standard_fields = dict((str(f), f) for f in Field.objects.all())
        
        for row in cursor.execute("SELECT ID,Name,DCElement,DCRefinement FROM FieldDefinitions"):
            dc = ('dc:%s%s%s' % (row.DCElement, row.DCRefinement and '.' or '', row.DCRefinement or '')).lower()
            if standard_fields.has_key(dc):
                fields[row.ID] = standard_fields[dc]
                print "+",
            else:
                fields[row.ID] = Field.objects.create(label=row.Name)
                print "-",
        print
     
        # Migrate records and media
        
        print "Migrating records"
        images = {}
        count = 0
        
        for row in cursor.execute("SELECT ID,CollectionID,Resource,Created,Modified,RemoteID," +
                                  "CachedUntil,Expires,UserID,Flags FROM Images"):
            if groups.has_key(row.CollectionID):
                images[row.ID] = Record.objects.create(created=row.Created or row.Modified or datetime.now(),
                                                       name=row.Resource.rsplit('.', 1)[0],
                                                       modified=row.Modified or datetime.now(),
                                                       source=row.RemoteID,
                                                       next_update=row.CachedUntil or row.Expires)
                GroupMembership.objects.create(record=images[row.ID], group=groups[row.CollectionID])
                if storage.has_key(row.CollectionID):
                    if row.Resource.endswith('.xml'):
                        self.process_xml_resource(images[row.ID], storage[row.CollectionID], row.Resource)
                    else:
                        for type in ('full', 'medium', 'thumb'):
                            Media.objects.create(
                                record=images[row.ID],
                                name=type,
                                url='%s/%s' % (type, row.Resource),
                                storage=storage[row.CollectionID],
                                mimetype='image/jpeg')          
                count += 1
                if count % 100 == 0:
                    print "%s\r" % count,
                if count >= IMPORT_RECORDS:
                    break

        # Migrate field values
        
        print "Migrating field values"
        count = 0
        
        for row in cursor.execute("SELECT ImageID,FieldID,FieldValue,OriginalValue,Type,Label " +
                                  "FROM FieldData INNER JOIN FieldDefinitions ON FieldID=FieldDefinitions.ID"):
            if images.has_key(row.ImageID):
                FieldValue.objects.create(record=images[row.ImageID],
                                          field=fields[row.FieldID],
                                          label=row.Label,
                                          value=row.FieldValue,
                                          type=row.Type == 2 and 'D' or 'T')
            count += 1
            if count % 100 == 0:
                print "%s\r" % count,
        
        
        # Migrate folders
        
        # todo
        
        # Migrate slideshows
            
        print "Migrating slideshows and slides"
        count = 0
        slideshows = {}
        for row in cursor.execute("SELECT ID,UserID,Title,Description FROM Slideshows"):
            slideshows[row.ID] = Group.objects.create(title=row.Title, owner=users[row.UserID],
                                                      type='presentation', description=row.Description)
        for row in cursor.execute("SELECT SlideshowID,ImageID,DisplayOrder,Scratch FROM Slides"):
            if images.has_key(row.ImageID):
                GroupMembership.objects.create(record=images[row.ImageID],
                                               group=slideshows[row.SlideshowID],
                                               order=row.DisplayOrder,
                                               hidden=row.Scratch)
            count += 1
            if count % 100 == 0:
                print "%s\r" % count,

        # Migrate slideshow permissions
        
        #Privilege.ModifyACL -> n/a
        #Privilege.ModifySlideshow -> write
        #Privilege.DeleteSlideshow -> manage
        #Privilege.ViewSlideshow -> read
        #Privilege.CopySlideshow -> n/a
        
        for row in cursor.execute("SELECT ObjectID,UserID,GroupID,GrantPriv,DenyPriv " +
                                  "FROM AccessControl WHERE ObjectType='S' AND ObjectID>0"):
            if not slideshows.has_key(row.ObjectID):
                continue
            ac = AccessControl()
            ac.content_object = slideshows[row.ObjectID]            
            if populate_access_control(ac, row, P['ViewSlideshow'], P['ModifySlideshow'], P['DeleteSlideshow']):
                ac.save()


        # Migrate system permissions
        
        # todo

    def process_xml_resource(self, record, storage, file):
        
        def node_text(node):
            return ''.join(n.nodeValue for n in node.childNodes).strip()
        
        def child_text(node, tagname):
            for e in node.getElementsByTagName(tagname):
                return node_text(e)
            return None
            
        def get_media(node):
            return dict(
                display = e.attributes['display'].nodeValue,
                type = e.attributes['type'].nodeValue,
                label = child_text(e, 'label'),
                link = child_text(e, 'link'),
                data = child_text(e, 'data'), )
        
        def make_html(link, label):
            if not link:
                return label
            else:
                return '<a href="%s">%s</a>' % (link, label)
        
        def name_from_url(url):
            return os.path.splitext(os.path.basename(urlparse(url)[2]))[0]
        
        try:
            ovcstorage = Storage.objects.get(name='onlinevideo')
        except Storage.DoesNotExist:
            ovcstorage = Storage.objects.create(title='Online Video Collection', name='onlinevideo', system='online')
        
        try:
            ovcstorage_full = Storage.objects.get(name='onlinevideo')
        except Storage.DoesNotExist:
            ovcstorage_full = Storage.objects.create(title='Online Video Collection (downloadable)', name='onlinevideo-full', system='online')
        
        description_field = Field.objects.get(standard__prefix='dc', name='description')
        
        file = os.path.join(storage.base, file)
        resource = minidom.parse(file)
        thumb = None
        medium = []
        full = []
        for e in resource.getElementsByTagName('thumb'):
            thumb = child_text(e, 'image')
        for e in resource.getElementsByTagName('medium'):
            medium.append(get_media(e))
        for e in resource.getElementsByTagName('full'):
            full.append(get_media(e))
        
        Media.objects.create(
            record=record,
            name='thumb',
            url='thumb/%s' % thumb,
            storage=storage,
            mimetype='image/jpeg')
        
        for m in medium:
            if m['display'] == 'default':
                record.fieldvalue_set.create(field=description_field, value=make_html(m['link'], m['label']))
            else:
                Media.objects.create(
                    record=record,
                    name=name_from_url(m['link']),
                    url=m['link'],
                    storage=ovcstorage,
                    mimetype=m['type'])

        for m in full:
            if m['display'] == 'default':
                record.fieldvalue_set.create(value=make_html(m['link'], m['label']))
            else:
                Media.objects.create(
                    record=record,
                    name=name_from_url(m['link']),
                    url=m['link'],
                    storage=ovcstorage_full,
                    mimetype=m['type'])
