
""" Methods shared by all UnitedSearch searchers """

from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from rooibos import settings_local
from rooibos.unitedsearch.external.translator.query_mod import query_mods
import re 
import json
import urllib2
import datetime

PROXY_URL="www-cache2.ecs.vuw.ac.nz:8080"

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
    print "query in bqs============"
    print query
    keywords = ""
    para_map = {}
    keywords = re.findall("(?<=keywords=)[^,]*", query) # here keywords contains a list
    print "keywords in break_query_string ===="
    print keywords
    if keywords and len(keywords) >= 1:
        keywords = keywords[0] #now keywords is a string from that list.
    else:
        keywords=""
    para_map = re.findall("(?<=params=).*", query)
    if para_map and len(para_map) >= 1:
        para_map = json.loads(para_map[0])
        #para_map = get_parameters(para_map[0])
    else:
        para_map = {}
    # default, if query didn't follow search=... structure, simply use query itself
    if keywords is "" and len(para_map) is 0 :
        keywords = query or ""
    print 'common - 68 keywords: ' +keywords
    print "final para_map in break_query_string"
    print para_map
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


        
def get_parameters(para_str) :
    print "start break:"+str(para_str)
    test = json.loads(para_str)
    print "test:"+str(test)
    if isinstance(test,dict):
        if len(test)>0:
            para_map = {}
            try:
                para_str = str(para_str)
                para_str = para_str[1:]
                para_str = para_str[:-1]
                print "para_str======"+para_str
                para_list = para_str.split(",")
                for para in para_list:
                    pair = para.split(":")
                    add_to_dict(para_map,pair[0].replace("\"",""),pair[1].replace("\"",""))
                print "para_map before return"
                print para_map
                return para_map
            except:
                return {}
        else:
            return {}
    else:
        return {}


def list_to_str(l) :
    s = ""
    if not isinstance(l,list):
        return str(l)
    else:
        for v in l:
            s+="+"+str(v)
        s = s[1:]
        return s
    
        
"""
Creates a ProxyHandler for the University Proxy
"""
def proxy_opener():
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, PROXY_URL, settings_local.username, settings_local.password)
    proxy_handler = urllib2.ProxyHandler({"http":PROXY_URL, "https":settings_local.username+":"+settings_local.password+"@"+PROXY_URL})
    proxy_auth_handler = urllib2.ProxyBasicAuthHandler(password_mgr)
    return urllib2.build_opener(proxy_handler, proxy_auth_handler)
  