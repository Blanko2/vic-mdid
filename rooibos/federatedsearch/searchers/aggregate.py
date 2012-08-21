from django.core.urlresolvers import reverse
from rooibos.federatedsearch.models import FederatedSearch

from rooibos.federatedsearch.searchers.external import digitalnz

def federatedSearchSource(searcher):
	class Search(FederatedSearch):
		def hits_count(self, keyword):
			return searcher.search(keyword, {}, 0, 0).total

		def get_label(self):
			return searcher.name

		def get_source_id(self):
			""" TODO """
			return "fake-source-id"

		def get_search_url(self):
			""" TODO """
			return reverse('dummy-search')
	return Search

searchers = [ digitalnz ]

test = federatedSearchSource(digitalnz)

def federatedSearchSources():
	print '*******'
	print test
	return [ test ]
#	return map(federatedSearchSource, searchers)
