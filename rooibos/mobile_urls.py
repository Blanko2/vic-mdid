from django.conf.urls.defaults import *
from rooibos.mobile.views import m_main

urls = [
    # needs SSL because of embedded login form, otherwise CSRF fails
    url(r'^$', m_main, {'HELP': 'frontpage', 'SSL': True}, name='m_main')
    ]

urlpatterns = patterns('', *urls)