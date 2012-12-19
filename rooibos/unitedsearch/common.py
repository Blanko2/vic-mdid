
""" Methods shared by all UnitedSearch searchers """

from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from rooibos import settings_local
import re 
import json
import urllib2
import datetime

PROXY_URL="www-cache2.ecs.vuw.ac.nz:8080"
API_KEY="sfypBYD5Jpu1XqYBipX8"

def get_collection():
	collection, created = Collection.objects.get_or_create(
		name='unitedsearch',
		defaults={
			'title': 'United Search collection',
			'hidden': True,
			'description': 'Collection for images retrieved through the United Search'
		})
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=collection, usergroup=authenticated_users, read=True)
	return collection


def get_storage():
	storage, created = Storage.objects.get_or_create(
		name='unitedsearch',
		defaults={
			'title': 'United Search collection',
			'system': 'local',
			'base': os.path.join(settings.AUTO_STORAGE_DIR, 'unitedsearch')
		})
	if created:
		authenticated_users, created = ExtendedGroup.objects.get_or_create(type=AUTHENTICATED_GROUP)
		AccessControl.objects.create(content_object=storage, usergroup=authenticated_users, read=True)
	return storage
	
	
#METHODS FOR EXTERNAL DATABASES =====================

def break_query_string(query):
    """
    Breaks query string into parameters and keywords 
    query is in form search=search_type, keywords=words (space-separated), params={"type": "value", ...}
    or 'word'
    """
    keywords = ""
    para_map = {}
    keywords = re.findall("(?<=keywords=)[^,]*", query) # here keywords contains a list
    if keywords and len(keywords) >= 1:
        keywords = keywords[0] #now keywords is a string from that list.
    else:
        keywords=""
    para_map = re.findall("(?<=params=).*", query)
    if para_map and len(para_map) >= 1:
        para_map = json.loads(para_map[0])
        para_map2 = {}
    else:
        para_map = {}
    # default, if query didn't follow search=... structure, simply use query itself
    if keywords is "" and len(para_map) is 0 :
        keywords = query or ""
    print 'common - 68 keywords: ' +keywords
    return keywords, para_map
    
#========Dictionary methods ========

def merge_dictionaries(dict1, dict2, valid_keys):
    """ Merges two dictionaries, a & b -> return b , checks if values in a are valid but assumes b is all valid as is program generated
    
    Keyword arguments:
    dict1 - user/search generated dictionary, values are checked using parameters in valid_keys
    dict2 - program generated dictionary, values are assumed correct -- all values so that views.py remembers defaults
    valid_keys - list of all keys accepted by the searcher, values used to check dict1's keys
    """
    unsupported_parameters = {}
    for key in dict1:
        newKey = key
        newKey2 = key.replace('-','')
        if newKey in valid_keys or newKey=='not':	# all types of parameter defined for this class
            # supported parameter type
            add_to_dict(dict2, newKey, dict1[key])
        elif newKey2 in valid_keys:	# all types of parameter defined for this class
            # supported parameter type
            add_to_dict(dict2, newKey, dict1[key])
        else :
            # unsupported, so add to list of errors, and treat value as a keyword
            add_to_dict(unsupported_parameters, key, dict1[key])
            add_to_dict(dict2, "All Words", dict1[key])
    return dict2, unsupported_parameters
    
def add_to_dict(dictionary, key, value):
    """ adds a key and value to given dict if the pair dont already exist """
    if isinstance(value, list):
        if len(value) == 0:	# if empty list, make sure entry exists anyway
            if not key in dictionary:
                dictionary[key] = []
        for v in value:
            add_to_dict(dictionary, key, v)
    else:
        if key in dictionary:
            if value not in dictionary[key]:
                dictionary[key].append(value)
        else:
            dictionary[key] = [value]	# want final result to be in a list
  
def getValue(dictionary, key):
    """ return either val at index=0 or "" if none """
    if key in dictionary:
        value = dictionary[key]
        if isinstance(value, list):
            value_string = ""
            for li in value:
                value_string += li+" "
                value = value_string.strip()
        else:
            value = str(value)
        return value
    else:
        return ""

"""
Creates a ProxyHandler for the University Proxy
"""
def proxy_opener():
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, PROXY_URL, settings_local.username, settings_local.password)
    proxy_handler = urllib2.ProxyHandler({"http":PROXY_URL, "https":settings_local.username+":"+settings_local.password+"@"+PROXY_URL})
    proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
    return urllib2.build_opener(proxy_handler, proxy_auth_handler)
  
#=============Helper Methods ============
#Takes a single date or date range and returns (date1, date2, error_msg) where dates are formatted
#    as per desired_format
"""
Supported incoming formats: "dd/mm/[yy]yy-dd/mm/[yy]yy" (permitted separators: "/", ":", "-")
				"[yy]yy-[yyy]y"
				"dd/mm/[yy]yy"
				"[yy]yy"
	Passing None or "" as date returns current date
	If no day or month is specified, returns jan 1st
	Note, doesn't support BC dates, or specification of BC, AD

    Supported outgoing formats: "ddmmyyyy", "mmddyyyy", "yyyy"
    
    Returns (startDate, endDate, error_msg) where startDate and endDate are formatted as requested
    Both dates are "" if date is unparsable or invalid
    error_msg is None unless error was found
    
    Note, date must be the entire string, or regices will break
    
    Pass default end date as a datetime.date object

def format_date(date, desired_format, separator, default_end=datetime.date.today(), two_dates_wanted=False):
  # first, check if date is year range only (simplest format)
  year_match = re.match("^((?P<y1_prefix>(\d{2}|\d{0}))(?P<y1_suffix>(\d{2}))(\w?\-\w?(?P<y2_prefix>(\d{2}|\d{0}))(?P<y2_suffix>(\d{1,2})))?)$", date)
  
  if year_match:
     date1_tuple,date2_tuple = _build_dates_from_year(year_match, default_end, two_dates_wanted)
  
  # next, try day format matching
  else:
      day_match = re.match("^((?P<d1>(\d{2}))(?P<separator>([-/:]))(?P<m1>(\d{2}))(?P=separator)(?P<y1_prefix>(\d{2}|\d{0}))(?P<y1_suffix>(\d{2}))(\w?\-\w?(?P<d2>(\d{2}))(?P=separator)(?P<m2>(\d{2}))(?P=separator)(?P<y2_prefix>(\d{2}|\d{0}))(?P<y2_suffix>(\d{2})))?)$", date)
      if day_match :
	date1_tuple,date2_tuple = _build_dates_from_day(day_match, default_end, two_dates_wanted)
      else:
	# dammit, unrecognised format
	return "", "", ("Date was unparsable: %s" %(date))

  # have date data, now validate it
  date1_tuple, date2_tuple, error_msg = _validate_date_range(date1_tuple, date2_tuple)
  
  if error_msg:
    return "", "", error_msg
  
  # and format
  date1, date2 = _format_dates(date1_tuple, date2_tuple, desired_format, separator)
  return date1, date2, None	# no error message
  

def _build_dates_from_year(year_match, default_end, two_dates_wanted):
    # build y1 data
    d1 = 1	# defaults
    m1 = 1
    y1_prefix = year_match.group("y1_prefix")
    y1_suffix = year_match.group("y1_suffix")
    if y1_prefix:
	y1 = int(y1_prefix + y1_suffix)
    else:
	y1_prefix = _get_default_year_prefix(int(y1_suffix))
	y1 = int(y1_prefix+y1_suffix)

    # build y2 data
    if two_dates_wanted:
	d2 = 31	# end of year for last year of date range - want to include whole year
	m2 = 12
	y2_prefix = year_match.group("y2_prefix")
	y2_suffix = year_match.group("y2_suffix")
	if y2_prefix and len(y2_suffix) > 1:	# have full date specified
	    y2 = int(y2_prefix + y2_suffix)
	elif y2_suffix:
	    # no prefix specified, use data from from date
	    if len(y2_suffix) is 2:
		y2 = int(y1_prefix+y2_suffix)
	    else:
		y2 = int( y1_prefix + y1_suffix[0:1] + y2_suffix)
	else:
	    # no second date specified, use default
	    y2 = str(default_end.year)

	return ((d1,m1,y1), (d2,m2,y2))
    else:
	return (d1,m1,y1), None



def _build_dates_from_day(day_match, default_end, two_dates_wanted):
    # build from year data
    d1 = int(day_match.group("d1"))
    m1 = int(day_match.group("m1"))
    y1_prefix = day_match.group("y1_prefix")
    y1_suffix = day_match.group("y1_suffix")
    if y1_prefix:
	y1 = int(y1_prefix + y1_suffix)
    else:
	y1_prefix = _get_default_year_prefix(int(y1_suffix))
	y1 = int(y1_prefix+y1_suffix)

    # build y2 data
    if two_dates_wanted:
	d2 = int(day_match.group("d2")) if day_match.group("d2") else default_end.day
	m2 = int(day_match.group("m2")) if day_match.group("m2") else default_end.month
	y2_prefix = day_match.group("y2_prefix")
	y2_suffix = day_match.group("y2_suffix")
	if y2_prefix:
	    y2 = int(y2_prefix + y2_suffix)
	elif y2_suffix:	# but not y2_prefix
	    y2_prefix = y1_prefix
	    y2 = int(y2_prefix + y2_suffix)
	else:		# no data specified
	    y2 = default_end.year
	return ((d1,m1,y1), (d2,m2,y2))
    else:
	return (d1,m1,y1), None

    
def _get_default_year_prefix(year_suffix):
  current_year = datetime.date.today().year
  if year_suffix <= current_year:
    return str(current_year)[0:2]	# prefix of current year
  else:
    return str(current_year-100)[0:2]	# previous century

    
# currently v simple checking, could update TODO
def _validate_date_range(date1_tuple, date2_tuple):
    if date1_tuple and date2_tuple:
	y1 = date1_tuple[2]
	y2 = date2_tuple[2]
	if y1 > y2:
	    return date1_tuple, date2_tuple, ("Date range cannot be negative: %s-%s" %(y1,y2))
    return date1_tuple, date2_tuple, None
  

def _format_dates(date1_tuple, date2_tuple, desired_format, separator):
    d1,m1,y1 = date1_tuple
    if date2_tuple:
	d2,m2,y2 = date2_tuple
    if desired_format is "ddmmyyyy":
	date1 = ("%s%s%s%s%s" %(d1,separator, m1, separator, y1))
	date2 = ("%s%s%s%s%s" %(d2,separator, m2, separator, y2)) if date2_tuple else None
	return date1,date2
    elif desired_format is "mmddyyyy":
	date1 = ("%s%s%s%s%s" %(m1,separator, d1, separator, y1))
	date2 = ("%s%s%s%s%s" %(m2,separator, d2, separator, y2)) if date2_tuple else None
	return date1,date2
    elif desired_format is "yyyy":
	date1 = str(y1)
	date2 = str(y2) if date2_tuple else None
	return date1, date2
    else:
	raise NotImplementedError("%s is not a supported date format (update unitedsearch.common._format_dates() if desired" %(desired_format))
"""
