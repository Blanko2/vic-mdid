import flickrapi
import urllib, urllib2, time
from os import makedirs
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.cache import cache
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from rooibos.data.models import Collection, CollectionItem, Record, FieldSet, Field
from rooibos.storage import Storage, Media
from rooibos.settings import FLICKR_KEY, FLICKR_SECRET
from forms import PeopleSearchForm
from rooibos.solr.models import SolrIndexUpdates 
from rooibos.solr import SolrIndex


flickr = flickrapi.FlickrAPI(FLICKR_KEY, FLICKR_SECRET, cache=True)


def _save_file(targeturl, base, filename):
    try:
        req = urllib2.Request(targeturl)
        response = urllib2.urlopen(req)
        try:
            makedirs(base)
        except Exception:
            pass
        image = open('%s/%s' % (base, filename), 'wb')
        image.write(response.read())
        image.close()
    except Exception, detail:
        print 'Error:', detail

def main(request):
    return render_to_response('flickr_main.html', {},
                              context_instance=RequestContext(request))

def authorize(request):
    return render_to_response('flickr_main.html', {},
                              context_instance=RequestContext(request))

def people(request, username=None):
    nsid = None
    if request.method == 'POST':
        form = PeopleSearchForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                e = flickr.people_findByUsername(username=username)
                nsid = e.find('user').attrib['nsid']
            except flickrapi.FlickrError:
                pass
    else:
        form = PeopleSearchForm()

    return render_to_response('flickr_people.html', {'form': form, 'nsid':nsid},
                              context_instance=RequestContext(request))


def photosets(request, id=None):
    try:
        if id:
            json = flickr.photosets_getList(user_id=id, format='json')
            e = flickr.photosets_getList(user_id=id)
            return render_to_response('flickr_sets.html', {'results': json},
                                          context_instance=RequestContext(request))
        else:
            pass
    except flickrapi.FlickrError:
        pass

def set(request, setid=None):
    try:
        if setid:
            extras = 'url_t, url_s, url_m, url_o'
            e = flickr.photosets_getPhotos(photoset_id=setid, extras=extras, format='json')
            return render_to_response('flickr_setphotos.html', {'results': e, 'setid': setid},
                                      context_instance=RequestContext(request))
        else:
            pass 
    except flickrapi.FlickrError:
        pass

def make_collection(request):
    storage = Storage.objects.get(name='flickr-full')
    collection = Collection()
    pass

def import_set_photos(request):
    setid = request.POST["setid"]
    try:
        if setid:
            e = flickr.photosets_getInfo(photoset_id=setid)
            title = e.find("photoset").find("title").text
            collection, created = Collection.objects.get_or_create(title=title, name=title)
            if created:
                collection.save()
                ms.append('Created Collection %s' % collection.title)

            extras = 'license, date_upload, date_taken, owner_name, icon_server, original_format, last_update, geo, tags, machine_tags, o_dims, views, media, path_alias, url_sq, url_t, url_s, url_m, url_o'
            e = flickr.photosets_getPhotos(photoset_id=setid, extras=extras)
            storage = Storage.objects.get(name='personal-images-full')
            for photo in e.find('photoset').findall('photo'):
                record = Record()
                record.fieldset = FieldSet.objects.get(name='dc')
                record.name = photo.attrib['title']
                record.save(force_insert=True)
                dc_identifier = Field.objects.get(name='identifier', standard__prefix='dc')
                dc_title = Field.objects.get(name='title', standard__prefix='dc')
                record.fieldvalue_set.create(field=dc_identifier, value=photo.attrib['id'])
                record.fieldvalue_set.create(field=dc_title, value=photo.attrib['title'])
                record.save()
                CollectionItem.objects.create(record=record, collection=collection).save()
                media = Media(record=record, 
                              name='full',
                              url = photo.attrib['url_o'].split('/')[-1],
                              storage = storage,
                              mimetype = 'image/jpeg',
                              width = photo.attrib['width_o'],
                              height = photo.attrib['height_o'])
                media.save()
                _save_file(photo.attrib['url_o'], storage.base, photo.attrib['url_o'].split('/')[-1])

                siu = SolrIndexUpdates(record=record.id)
                siu.save()
            si = SolrIndex()
            si.index()
            return render_to_response('flickr_setphotos.html', {'results': e},
                                      context_instance=RequestContext(request))
        else:
            pass 
    except flickrapi.FlickrError:
        pass

