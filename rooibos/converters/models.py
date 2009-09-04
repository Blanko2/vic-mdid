import flickrapi
import urllib, urllib2, time, subprocess, re, os, sys, shutil, settings
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.solr.models import SolrIndexUpdates
from rooibos.solr import SolrIndex
from rooibos.access.models import AccessControl
from django.conf import settings

class PowerPointUploader:

    def convert_ppt(self,title,img_count,ppt):
        filename = ppt.split('/')[-1]
        path = re.sub(filename, "", ppt)
        # Remove quotes and spaces from the title (This could be better managed)
        safe_title = re.sub(" ", "-", title)
        safe_title = re.sub("'", "", safe_title)
        safe_title = re.sub('"', "", safe_title)
        # Use "Save Title" as part of the temp directory path to prevent toe stepping
        temp_path = path + safe_title + "/"
        img_count = int(img_count)
        try:
            if not os.path.isdir(temp_path):
                os.mkdir(temp_path)
            # Call Open Office via the command line in order to convert Power Point Slides to Images
            strCmd = '"' + '"' + settings.OPEN_OFFICE_PATH + 'python.exe" "' + settings.OPEN_OFFICE_PATH + 'DocumentConverter.py" "' + ppt + '" "' + temp_path + filename.split('.')[0] + '.html" Width=1024 Format=2' + '"'
            p = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            # DIsplay Errors if the exist
            for line in p.stdout.readlines():
                print line,
            retval = p.wait()
            # Import the images created
            while img_count > 0:
                img_count = img_count-1
                shutil.move(temp_path + "img"+str(img_count)+".jpg", temp_path + safe_title+"-img"+str(img_count)+".jpg")
                self.import_image(temp_path + safe_title+"-img"+str(img_count)+".jpg",title,safe_title)
        except Exception, detail:
            print 'Error:', detail
        finally:
            # Delete Power Point Slides and Image Files
            #os.remove(ppt)
            print temp_path
            #shutil.rmtree(temp_path)

    def import_image(self, source, title, safe_title):
        try:
            collection, created = Collection.objects.get_or_create(title='Personal Images', name='personal-images')
            if created:
                collection.save()

            storage = Storage.objects.get(name='personal-images-full')

            record = Record()
            record.fieldset = FieldSet.objects.get(name='dc')
            record.name = source.split('/')[-1].split('.')[0]
            record.save(force_insert=True)
            CollectionItem.objects.create(record=record, collection=collection).save()

            AccessControl.objects.create(content_object=record, read=True)
            dc_identifier = Field.objects.get(name='identifier', standard__prefix='dc')
            dc_title = Field.objects.get(name='title', standard__prefix='dc')
            record.fieldvalue_set.create(field=dc_identifier, value=str(time.time()))
            record.fieldvalue_set.create(field=dc_title, value=title)
            record.save()

            media = Media(record=record,
                          name='full',
                          url=source.split('/')[-1],
                          storage=storage,
                          mimetype='image/jpeg')
            media.save()
            _save_file(source, storage.base, source.split('/')[-1])

            siu = SolrIndexUpdates(record=record.id)
            siu.save()
        except Exception, detail:
            print 'Error:', detail
        return dict(record=record, media=media)

class ImageConverter:
    def convert_images(self,ppt_file,images):
        imageStr = ""
        for image in images:
            imageStr = imageStr + ' "' + image + '"'
        strCmd = '"' + '"' + settings.OPEN_OFFICE_PATH + 'python.exe" "' + settings.OPEN_OFFICE_PATH + 'ImageConverter.py" "' + settings.STATIC_DIR+"ppt/"+ppt_file + '" ' + imageStr + '"'
        print strCmd
        p = subprocess.Popen(strCmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # Display Errors if they exist
        for line in p.stdout.readlines():
            print line,
        retval = p.wait()

def _save_file(targeturl, base, filename):
    try:
        try:
            makedirs(base)
        except Exception:
            pass
        shutil.move(targeturl, base+"/"+filename)
    except Exception, detail:
        print 'Error:', detail
