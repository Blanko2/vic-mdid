from external import digitalnz, nga, flickr, gallica, collectiveaccess, artstor, trove

""" UnitedSearchers to search. Must have name and identifier attributes defined"""
all = [
	nga,
	digitalnz,
	flickr,
	gallica,
    collectiveaccess,
    #artstor,
	#trove
]
"""
- Trove is not working as intended, the urls returned by trove API are not links to images, 
    but to pages that contain the image. As such, while there is a method in trove code to get 
    some of the images out, it does not work for all of them, and so we disabled trove while 
    we work on the issue
- Artstor is not working atm either, due to the method of access which ran through uni
    and does not have that option right now
"""
