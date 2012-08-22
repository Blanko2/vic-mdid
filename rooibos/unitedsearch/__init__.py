class Result:
	def __init__(self, total, nextoffset):
		self.nextoffset = nextoffset
		self.total = total
		self.images = []

	def addImage(self, image):
		self.images += [image]

class Image:
	def __init__(self, url, thumb, name, meta, identifier):
		self.url = url
		self.thumb = thumb
		self.name = name
		self.meta = meta
		self.identifier = identifier

class Parameter:
	def __init__(self, name, type):
		self.name = name
		self.type = type
