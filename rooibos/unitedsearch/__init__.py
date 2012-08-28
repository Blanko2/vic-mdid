class Result:
	""" Holds the image-metadata pairs found by a search of a database. """
	
	def __init__(self, total, nextoffset):
		""" total is how many images were found by the search. Note,
		the actual Result object doesn't store all of them, only some"""
		self.nextoffset = nextoffset
		self.total = total
		self.images = []

	def addImage(self, image):
		self.images += [image]


class Image:
	""" A single image-metadata pair"""
	
	def __init__(self, url, thumb, name, meta, identifier):
		""" url is path to just the image
		thumb is url to the thumbnail
		meta is a dictionary of any useful info about this image
		identifier is sufficient info to find this image again """
		self.url = url
		self.thumb = thumb
		self.name = name
		self.meta = meta
		self.identifier = identifier


class Parameter:
	""" Essentially a search filter applicable to the given database"""
	
	def __init__(self, name, type):
		""" eg name = 'from nz': type = boolean """
		self.name = name
		self.type = type
