from django.core.urlresolvers import reverse
from rooibos.federatedsearch.models import FederatedSearch

import searchers

def federatedSearchSource(searcher):
	
	class Search(FederatedSearch):
		def hits_count(self, keyword):
            #Todo: Pass keyword into Translator
			"""
			numHits = searcher.search(keyword, {}, 0, 0)
			if not numHits:
			  return 0
			return numHits[0].total
			"""
			#once the count method is implemented in each database, 
			# switch to this:
			return searcher.count(keyword)

		def get_label(self):
			return searcher.name

		def get_source_id(self):
			return "united-%s" % searcher.identifier

		def get_search_url(self):
			return reverse('united:searchers:%s:search' % searcher.identifier)
	return Search

def federatedSearchSources():
	""" Wraps the UnitedSearch searchers from searchers.py
	into FedaratedSearch, so they can be displayed etc """
	return map(federatedSearchSource, searchers.all)
