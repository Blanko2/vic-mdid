import json
from itertools import *
from . import *

class searcherUnion:
	def __init__(self, searchers):
		self.searchers = searchers
		self.name = ", ".join([s.name for s in searchers])
		self.identifier = ",".join([s.identifier for s in searchers])
		self.parameters = MapParameter(dict([(str(si), OptionalParameter(searchers[si].parameters, searchers[si].name)) for si in range(len(searchers))]))

	def search(self, term, params, off, leng):
		if str(off) == "0":
			off = [0]*len(self.searchers)
		else:
			off = json.loads(off)
		# TODO: better maths so the amount of results isn't off by a few due to flooring
		leng = leng/len([o for o in off if o != None])
		results = []
		for (s, o, si) in zip(self.searchers, off, range(len(self.searchers))):
			if o != None:
				results += [(s, s.search(term, params[str(si)][0] if len(params[str(si)]) > 0 else None, o, leng))]
			else:
				results += [(s, None)]
		#results = [(s, s.search(term, params[str(si)][0] if len(params[str(si)]) > 0 else None, o, leng)) if o != None else None for (s, o, si) in zip(self.searchers, off, range(len(self.searchers)))]
		result = Result(sum([r.total if r else 0 for (_, r) in results]), json.dumps([r.nextoffset if r else None for (_, r) in results]))
		# NOTE: map works, imap doesn't .. no list-comprehension-expression scope
		for (se, im) in ifilter(None, chain(*izip_longest(*[map(lambda i: (s, i), r.images) for (s, r) in results if r]))):
			result.addImage(im.withIdentifier(json.dumps([se.identifier, im.identifier])))
		return result
	
	def getImage(self, identifier):
		i = json.loads(identifier)
		searcher = next(dropwhile(lambda s: s.identifier != i[0], self.searchers))
		img = searcher.getImage(i[1])
		return img.withIdentifier(json.dumps([searcher.identifier, img.identifier]))
