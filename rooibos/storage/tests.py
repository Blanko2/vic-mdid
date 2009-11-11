from __future__ import with_statement
import unittest
import tempfile
import os.path
import Image
import shutil
from StringIO import StringIO
from django.test.client import Client
from django.core.files import File
from django.utils import simplejson
from rooibos.data.models import *
from rooibos.storage.models import Media, ProxyUrl, Storage, TrustedSubnet
from localfs import LocalFileSystemStorageSystem
from rooibos.storage import get_thumbnail_for_record, get_image_for_record
from rooibos.access.models import AccessControl
from rooibos.presentation.models import Presentation, PresentationItem


class LocalFileSystemStorageSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test', name='test', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        self.record.delete()
        self.storage.delete()
        self.collection.delete()

    def test_save_and_retrieve_file(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='image', storage=self.storage)
        content = StringIO('hello world')
        media.save_file('test.txt', content)

        self.assertEqual('test.txt', media.url)

        content = media.load_file()
        self.assertEqual('hello world', content.read())

        media.delete()

    def test_thumbnail(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        thumbnail = get_thumbnail_for_record(self.record)
        self.assertTrue(thumbnail.width == 100)
        self.assertTrue(thumbnail.height < 100)

        media.delete()

    def test_derivative_permissions(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        user1 = User.objects.create(username='test1890723589075')
        user2 = User.objects.create(username='test2087358972359')

        AccessControl.objects.create(content_object=self.collection, user=user1, read=True)
        AccessControl.objects.create(content_object=self.collection, user=user2, read=True)

        AccessControl.objects.create(content_object=self.storage, user=user1, read=True)
        AccessControl.objects.create(content_object=self.storage, user=user2, read=True,
                                     restrictions=dict(width=200, height=200))

        result1 = get_image_for_record(self.record, width=400, height=400, user=user1)
        result2 = get_image_for_record(self.record, width=400, height=400, user=user2)

        self.assertEqual(400, result1.width)
        self.assertEqual(200, result2.width)

        result3 = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(result2.id, result3.id)

        media.delete()


    def test_access_through_presentation(self):
        Media.objects.filter(record=self.record).delete()
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

        user1 = User.objects.create(username='test3097589074404')
        user2 = User.objects.create(username='test4589570974047')

        AccessControl.objects.create(content_object=self.collection, user=user1, read=True)
        storage_acl = AccessControl.objects.create(content_object=self.storage, user=user1, read=True)

        presentation = Presentation.objects.create(title='test47949074', owner=user1)
        presentation.items.create(record=self.record, order=1)

        # user2 has no access to storage or collection, so should not get result
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(None, result)

        # give access to presentation
        AccessControl.objects.create(content_object=presentation, user=user2, read=True)

        # user2 has no access to storage yet, so still should not get result
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(None, result)

        # give user2 access to storage
        user2_storage_acl = AccessControl.objects.create(content_object=self.storage, user=user2, read=True)

        # now user2 should get the image
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(400, result.width)

        # password protect the presentation
        presentation.password='secret'
        presentation.save()

        # user2 has not provided presentation password, so should not get result
        result = get_image_for_record(self.record, width=400, height=400, user=user2)
        self.assertEqual(None, result)

        # with presentation password, image should be returned
        result = get_image_for_record(self.record, width=400, height=400, user=user2,
                                      passwords={presentation.id: 'secret'})
        self.assertEqual(400, result.width)



class ImageCompareTest(unittest.TestCase):

    def test_compare(self):
        from rooibos.storage import _imgsizecmp

        class image:
            def __init__(self, w, h):
                self.width = w
                self.height = h

        data = [image(w, h) for w in (10, None, 20) for h in (15, 5, None)]

        data = sorted(data, _imgsizecmp)[::-1]


        self.assertEqual(data[0].width, 20)
        self.assertEqual(data[0].height, 15)

        self.assertEqual(data[1].width, 10)
        self.assertEqual(data[1].height, 15)

        self.assertEqual(data[2].width, 20)
        self.assertEqual(data[2].height, 5)

        self.assertEqual(data[3].width, 10)
        self.assertEqual(data[3].height, 5)


class ProxyUrlTest(unittest.TestCase):

    def setUp(self):
        self.user = User.objects.create(username='proxytest')
        self.user.set_password('test')
        self.user.save()
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test', name='test', system='local', base=self.tempdir)
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, user=self.user, read=True,
                                     restrictions=dict(width=50, height=50))
        AccessControl.objects.create(content_object=self.collection, user=self.user, read=True)
        media = Media.objects.create(record=self.record, name='tiff', mimetype='image/tiff', storage=self.storage)
        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif'), 'rb') as f:
            media.save_file('dcmetro.tif', f)

    def tearDown(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        self.record.delete()
        self.storage.delete()
        self.collection.delete()
        self.user.delete()


    def test_proxy_url(self):

        c = Client()
        response = c.post('/media/proxy/create/')
        # Response is JSON, should always be 200
        self.assertEqual(200, response.status_code)
        # Result should be error since we did not provide any credentials
        data = simplejson.loads(response.content)
        self.assertEqual('error', data['result'])

        login = c.login(username='proxytest', password='test')
        self.assertTrue(login)

        TrustedSubnet.objects.create(subnet='127.0.0.1')

        response = c.post('/media/proxy/create/',
                          {'url': self.record.get_thumbnail_url(), 'context': '_1_2'},
                          HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        data = simplejson.loads(response.content)
        self.assertEqual('ok', data['result'])
        id = data['id']
        c.logout()

        # try to retrieve content
        url = '/media/proxy/%s/' % id
        response = c.get(url, {'context': '_1_2'})
        self.assertEqual(200, response.status_code)
        self.assertEqual('image/jpeg', response['content-type'])

        # make sure image dimension restrictions took effect
        image = Image.open(StringIO(response.content))
        width, height = image.size
        self.assertEqual(50, width)


    def test_duplicate_proxy_url(self):

        TrustedSubnet.objects.create(subnet='127.0.0.1')
        proxy_url = ProxyUrl.create_proxy_url('/some/url', 'ctx1', '127.0.0.1', self.user)
        proxy_url2 = ProxyUrl.create_proxy_url('/some/url', 'ctx2', '127.0.0.1', self.user)
        proxy_url3 = ProxyUrl.create_proxy_url('/some/url', 'ctx1', '127.0.0.1', self.user)
        self.assertEqual(proxy_url.uuid, proxy_url3.uuid)
        self.assertNotEqual(proxy_url.uuid, proxy_url2.uuid)


class OnlineStorageSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test', name='test', system='online')
        self.record = Record.objects.create(name='monalisa')
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        self.record.delete()
        self.storage.delete()
        self.collection.delete()

    def test_retrieval(self):
        url = "file:///" + os.path.join(os.path.dirname(__file__), 'test_data', 'dcmetro.tif').replace('\\', '/')
        media = Media.objects.create(record=self.record, storage=self.storage, url=url, mimetype='image/tiff')
        thumbnail = get_thumbnail_for_record(self.record)
        self.assertTrue(thumbnail.width == 100)
        self.assertTrue(thumbnail.height < 100)

        media.delete()


class StreamingStorageSystemTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.collection = Collection.objects.create(title='Test')
        self.storage = Storage.objects.create(title='Test',
                                              name='test',
                                              system='streaming',
                                              base=self.tempdir,
                                              urlbase='file:///' + self.tempdir.replace('\\', '/'))
        self.record = Record.objects.create(name='record')
        self.media = Media.objects.create(record=self.record, name='image', storage=self.storage)
        CollectionItem.objects.create(collection=self.collection, record=self.record)
        AccessControl.objects.create(content_object=self.storage, read=True)
        AccessControl.objects.create(content_object=self.collection, read=True)

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        self.record.delete()
        self.storage.delete()
        self.collection.delete()

    def test_streaming(self):
        TEST_STRING = 'Hello world'
        content = StringIO(TEST_STRING)
        self.media.save_file('test.txt', content)
        c = Client()
        response = c.get(self.media.get_absolute_url())
        self.assertEqual(TEST_STRING, response.content)

