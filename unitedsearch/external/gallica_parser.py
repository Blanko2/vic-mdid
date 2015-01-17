"""
Parses parameters received from sidebar search for gallica 

Built separately as Gallica has idiosyncracies with its advanced
search - Gallica only accepts 5 advanced terms total and we use 
one of them as keywords always
Because of this and the way Gallica deals with operators, the 
parser deserved its own module
"""
from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from rooibos.unitedsearch.common import *
import re 
import json


def parse_gallica_sidebar(params):
        
        header = "field"
        tail = "_opt"
        i = 0
        type_key = "field0_type"
        value_key = "field0_value"
        opt_key = "field0"
        query_list=[]
        while i<5 :
            if i>0:
                type_key = "field"+str(i)+"_type"
                value_key = "field"+str(i)+"_value"
                opt_key = "field"+str(i)
            if type_key and value_key in params:
                field_type = params[type_key]
                value  = params[value_key]
                if opt_key in params:
                    opt = params[opt_key]
                else:
                    opt = "and"
                if field_type and value and not value=="":
                    entry = [field_type,value,opt]
                    query_list = add_entry(query_list,entry)
            if type_key in params:
                del params[type_key]
            if value_key in params:
                del params[value_key]
            if opt_key in params:
                del params[opt_key]
            i += 1
        
        params.update({"query_list":query_list})
        return None,params

def parse_gallica_adv_search(params):
    #print "params gallica parser"
    #print params
    query_list = []
    temp_params = params.copy()
    for key in params:
        opt = 'and'
        fixed_key = key
        if '_' in key:
                pair = key.split('_')
                opt = pair[0]
                fixed_key = pair[1]
        if fixed_key in field_types:
            entry = [fixed_key, params[key], opt]
            query_list = add_entry(query_list, entry)
            del temp_params[key]
    temp_params.update({"query_list":query_list})
    params = temp_params
    return None, params


def add_entry(query_list,entry):
    ql = query_list
    if entry[2]=="and":
        ql.insert(0,entry)
    else:
        ql.append(entry)
    return ql

def parse_gallica(params):
    if not params:
        return None, None

    if "all" in params and len(params)==1:
        return params['all'],None
    else:
        return parse_gallica_adv_search(params)

        



def add_keyword_to_params(keywords,params):
    if not "all" in params:
        if keywords and not keywords =="":
            params.update({"all":keywords})
    else:
        kw = params["all"]
        kw += "+"+keywords
        params.update({"all":kw})
    return params

def add_string(kw, string):
    if string =="":
        return kw
    if kw=="":
        kw += string
    else:
        kw += "+"+string
    return kw
        
def merge_query_list(keyword_list, max_size):
    temp_keyword_list = keyword_list
    kw=""
    not_kw=""
    for keyword in keyword_list :
        if keyword[0]==filter_type_map["all"] and keyword[2]==opt_type_map["and"]:
            kw = add_string(kw,keyword[1])
            temp_list.remove(keyword)
        elif keyword[0]==filter_type_map["all"] and keyword[2]==opt_type_map["exept"]:
            not_kw = add_string(not_kw,keyword[1])
            temp_keyword_list.remove(keyword)
    kw_size =0
    not_size=0
    if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
        kw_size =1
    if not not_kw=="":
        not_size=1
    size = len(temp_keyword_list)+kw_size+not_size
    while size>max_size:
       element = temp_keyword_list.pop()
       if element[2]==opt_type_map["and"]:
           kw = add_string(kw,element[1])
       else:
           not_kw = add_string(not_kw,element[1])
       if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
            kw_size =1
       if not not_kw=="":
            not_size=1
       size = len(temp_keyword_list)+kw_size+not_size  
    if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
       temp_keyword_list.insert(0,[filter_type_map["all"],kw,opt_type_map["and"]])
    if not not_kw=="":
       temp_keyword_list.append([filter_type_map["all"],not_kw,opt_type_map["except"]])

def merge_query_list(keyword_list):
    temp_keyword_list = keyword_list
    kw=""
    not_kw=""
    for keyword in keyword_list :
        if keyword[0]==filter_type_map["all"] and keyword[2]==opt_type_map["and"]:
            kw = add_string(kw,keyword[1])
            temp_list.remove(keyword)
        elif keyword[0]==filter_type_map["all"] and keyword[2]==opt_type_map["exept"]:
            not_kw = add_string(not_kw,keyword[1])
            temp_keyword_list.remove(keyword)
    kw_size =0
    not_size=0
    if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
        kw_size =1
    if not not_kw=="":
        not_size=1
    size = len(temp_keyword_list)+kw_size+not_size
    while size>5:
       element = temp_keyword_list.pop()
       if element[2]==opt_type_map["and"]:
           kw = add_string(kw,element[1])
       else:
           not_kw = add_string(not_kw,element[1])
       if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
            kw_size =1
       if not not_kw=="":
            not_size=1
       size = len(temp_keyword_list)+kw_size+not_size  
    if temp_keyword_list[0][2]==opt_type_map["except"] or not kw=="":
       temp_keyword_list.insert(0,[filter_type_map["all"],kw,opt_type_map["and"]])
    if not not_kw=="":
       temp_keyword_list.append([filter_type_map["all"],not_kw,opt_type_map["except"]])

def list_to_str(l):
    v = ""
    for e in l:
       if not v=="":
           v +="+"
       v += e
    return v

opt_map = {
    'and':'',
    'or':'?',
    'except':'-'
    }    

opt_type_map = {
    '':'and',
    '?':'or',
    '-':'except'
    }
    
valid_keys=["start date",
    "end date",
    "languages",
    "copyright",
    "all",    
    "artist",
    "title",
    "content",
    "table Of contents or captions",
    "subject",
    "source",
    "bibliographic record",
    "publisher",
    "isbn",
    "not"]

field_types = ["all","artist", "title", "content", "table of contents or captions", "subject", "source", "bibliographic record", "publisher", "isbn"]
