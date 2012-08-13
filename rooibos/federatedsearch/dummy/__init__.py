from django.core.urlresolvers import reverse
from rooibos.federatedsearch.models import FederatedSearch, HitCount

class Dummy(FederatedSearch):
	def hits_count(self, keyword):
		return 4
	
	def get_label(self):
		return "Dummy"

	def get_source_id(self):
		return "DUM"
	
	def get_search_url(self):
		print "** REVERSE: %s" % reverse('dummy-search')
		return reverse('dummy-search')
