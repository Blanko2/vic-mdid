from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from rooibos.unitedsearch.common import *
import re 
import json


def build_query(params):
        print "start"
        print params
        query = ""
        para_map = {}
        temp_params = params.copy()
        i = 0
        type_key = "field0_type"
        value_key = "field0_value"
        opt_key = "field0"
        query_list=[]
        while i<5 :
            if i>0:
                type_key = "field"+str(i)+"_opt_type"
                value_key = "field"+str(i)+"_opt_value"
                opt_key = "field"+str(i)+""
            if type_key and value_key in params:
                field_type = params[type_key]
                value  = str(params[value_key])
                opt = ""
                if opt_key in params:
                    opt = opt_map[params[opt_key]]
                if field_type and value and not value=="":
                    print field_type
                    print value
                    entry_key= str(opt+field_type)
                    para_map = update_para_map(para_map,entry_key,value)
            if type_key in params:
                del params[type_key]
            if value_key in params:
                del params[value_key]
            if opt_key in params:
                del params[opt_key]
            i += 1
        print "para_map"
        print para_map
        for entry_key in params:
            value = params[entry_key]
            if isinstance(value,list):
                value = value[0]
            if not value =='':
                para_map = update_para_map(para_map,entry_key,value)
        kw = ""
        if "all" in para_map:
            kw = para_map["all"]
            del para_map["all"]
        query = "keywords="+kw+",params="+str(para_map)
        query = query.replace('\'','\"').replace('u\"','\"')
        print "gallica query"
        print query
        return query
    
def update_para_map(para_map,key,value):
    if not key in para_map:
        para_map.update({key:value})
    else:
        value = para_map[key]+"+"+value
        para_map.update({key:value})
    return para_map

def parse_params(query, params):
    for key in query:
        if key.startswith("i_"):
            params.update({key.replace("i_",''):query[key]})
    return params





def parse_gallica_sidebar(params):
        print "original params"
        print params
        header = "field"
        tail = "_opt"
        i = 0
        type_key = "field0_type"
        value_key = "field0_value"
        opt_key = "field0"
        query_list=[]
        while i<5 :
            if i>0:
                type_key = "field"+str(i)+"_opt_type"
                value_key = "field"+str(i)+"_opt_value"
                opt_key = "field"+str(i)+"_opt"
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
        print "params in parser"
        print params
        return None,params

def parse_gallica_adv_search(params):
    query_list = []
    temp_params = params.copy()
    for key in params:
        if key in field_types:
            opt = ''
            fixed_key = key
            if key.startswith('-') or key.startswith('?'):
                opt = key[0]
                fixed_key = key[1:]
            entry = [fixed_key, params[key], opt_type_map[opt]]
            query_list = add_entry(query_list, entry)
            del temp_params[key]
    temp_params.update({"query_list":query_list})
    params = temp_params
    return None, params
                
        
"""        
def parse_gallica_adv_search(params):
    query_list = []
    temp_params = params.copy()
    for key in params:
        print "params"
        print params
        fixed_key = key
        opt = "and"
        value = params[key]
        if isinstance(value, list):
            value = value[0]
    if key in params        :
        temp_params.update({key:value})
    else:
        value = para_map[key]+"+"+value
        temp_params.update({key:value})

        value = list_to_str(value)
        if key.startswith('-'):
            opt = "except"
            fixed_key = key[1:]
        if key in field_types:
            entry = [fixed_key, value, opt]
            query_list = add_entry(query_list,entry)
            del temp_params[key]
        elif not opt=="and":
            del temp_params[key]
            
    params = temp_params
    if len(query_list)>5:
       query_list = merge_query_list(query_list)
    params.update({"query_list":query_list})
    return None, params
"""

def add_entry(query_list,entry):
    ql = query_list
    if entry[2]=="and":
        ql.insert(0,entry)
    else:
        ql.append(entry)
    return ql

def parse_gallica(keywords, params):
    # Case1: advansed search called from side bar
    """
    if "field0_type" in params:
        return parse_gallica_sidebar(params)
    params = {}
    print query
    keywords,para_map = break_query_string(query)
    params, unsupported_parameters = merge_dictionaries(para_map, params, valid_keys)
    keywords, params = remove_all_words(keywords,params)
    #Case 2: simple search
    """
    if params=={}:
        return keywords, None
    
    #Case 3: regular adv search
    params = add_keyword_to_params(keywords,params)
    return parse_gallica_adv_search(params)
"""
def remove_all_words(keywords,params):
    if "All Words" in params:
        if not keywords=="":
            keywords += "+"
        kw = params["All Words"]
        if isinstance(kw,list):
            kw = kw[0]
        keywords += kw
        del params["All Words"]
    return keywords,params
"""
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
