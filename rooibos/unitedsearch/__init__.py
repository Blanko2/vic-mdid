class Result:
	def __init__(self, total, nextoffset):
		self.nextoffset = nextoffset
		self.total = total
		self.images = []

	def addImage(self, image):
		self.images += [image]

class Image:
	def __init__(self, url, thumb, name, meta):
		self.url = url
		self.thumb = url
		self.name = name
		self.meta = meta

class Parameter:
	def __init__(self, name, type):
		self.name = name
		self.type = type
