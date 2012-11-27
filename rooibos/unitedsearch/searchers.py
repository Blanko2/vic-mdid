from external import digitalnz_searcher, nga, flickr, gallica, local, artstor

""" UnitedSearchers to search. Must have name and identifier attributes defined"""
all = [
	nga,
	digitalnz_searcher,
	#flickr, TODO: maybe implement later
	gallica,
	local,
	artstor,
]
