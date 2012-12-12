from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
import re 
import json
import datetime
#from rooibos.unitedsearch.external.translator.query_language import *

"""
This class parse request and return global query in form (keywords, params)

Case 1: Adv Search interface /  union search query string: keywords="...",params={...}
    pass to translator
    
Case 2: Adv Search from searcher sidebar
    Parse here and return global query

Case 3: User input query from searcher sidebar
    Parse here to build query string
    Pass query string to translator

"""

def parse(request, identifier):
    
    query = request.GET.get('q', '') or request.POST.get('q', '')
    
    if query and "=" in query and not "params={" in query:
        # Case : User input query language
        query = parse_query_language(query)
        #Todo : pass to translator
        return {"all":"cat"}
    elif query:
        #Todo : pass to translator
        return {"all":"cat"}
    else :
        return parse_sidebar(request,identifier)

def parse_sidebar(request,identifier):
    params = get_params(request)
    if identifier in complex_searcher:
        print "pass to complex_sidebar"
        return parse_complex_sidebar(params)
    else:
        return parse_regular_sidebar(params)

# Parse query for sidebar contains UserDefinedTypeParameter: gallica, trove
def parse_complex_sidebar(params):
        print "start"
        print params
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
        return para_map

#Parse regular sidebar         
def parse_regular_sidebar(params):
        for key in params:
            if isinstance(params[key],list):
                    params.update({key:params[key][0]})
        return params
        
def parse_query_language(query):        
            kw = ""
            par = ""
            not_query = ""
            query_list = query.split(',')
            for q in query_list:
                if "=" in q:
                    key_value = q.split("=")
                    key = key_value[0]
                    value = key_value[1]
                    del key_value[0]
                    del key_value[0]
                    if len(key_value)>0 :
                        for v in key_value:
                            value += "+"+v
                    if not par=="":
                        par +=","
                    if value.startswith("+"):
                        del value[0]
                    while value.endswith('\\'):
                        value = value[:-1]
                    par += "\""+key+"\":\""+value+"\""
            else:
                    if not kw=="":
                        kw += "+"
                    kw += q
            while kw.endswith('\\'):
                kw = kw[:-1]
            if not not_query == "":
                if not par == "":
                    par += ","
                par += not_query
            query = "keywords="+kw+",params={"+par+"}"
            return {"all":"cat"}



def build_query_language_from_sidebar(keywords,params):
    query = ""
    if not keywords and not params:
        return ""
    if keywords and params == {}:
        return keywords
    if keywords:
        query += keywords
    for key in params:
        if not query ==  "":
            query += ','
        query += key+"="+params[key]
    return query
    
def update_para_map(para_map,key,value):
    if not key in para_map:
        para_map.update({key:value})
    else:
        value = para_map[key]+"+"+value
        para_map.update({key:value})
    return para_map                
            
def get_params(request):
        params = {}
        for key in request.GET:
            if key.startswith('i_'):
                params.update({key[2:]:request.GET[key]})
        keys = params.keys()
        for key in keys:
            key2 = key+"_opt"
            if key in params and key2 in params:
                params.update({key:params[key2]})
                del params[key2]
        return params    
        

all_words_map = {
    'gallica' : 'all',
    'nga' : 'all words'
}

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
    

complex_searcher = ["gallica", "trove"]