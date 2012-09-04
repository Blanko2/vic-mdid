import json
import urllib2
from rooibos.unitedsearch import *
from urllib import urlencode
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from rooibos.data.models import Record

name = "Local"
identifier = "local"

def search(term, params, off, len):
	from rooibos.solr.views import run_search
	sobj = run_search(AnonymousUser(),
		keywords=term,
		sort="title_sort desc",
		page=int(off/len if len > 0 else 0) + 1,
		pagesize=len)
	hits, records = sobj[0:2]
	result = Result(hits, off + len)
	for i in records:
		result.addImage(ResultRecord(i, str(i.id)))
	return result

def getImage(identifier):
	i = int(identifier)
	return ResultRecord(Record.filter_one_by_access(AnonymousUser(), i), identifier)
