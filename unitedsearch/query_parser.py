from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from rooibos.unitedsearch.external.translator.query_mod import query_mods
from common import *
import re 
import json
import datetime
#TODO -- cast to string!
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
    
    if query and not "params={" in query:
        # Case : User input query language
        query = parse_query_language(query)
        #Todo : pass to translator
        return query,None
    elif query:
        #Todo : pass to translator
        return query, None
    else :
        return parse_sidebar(request,identifier)

def parse_sidebar(request,identifier):
    params = get_params(request)
    if identifier in complex_searcher:
        return parse_complex_sidebar(params,identifier)
    else:
        return parse_regular_sidebar(params)

# Parse query for sidebar contains UserDefinedTypeParameter: gallica, trove
def parse_complex_sidebar(params,identifier):
        para_map = {}
        temp_params = params.copy()
        i = 0
        type_key = "field0_type"
        value_key = "field0_value"
        opt_key = "field0"
        query_list=[]
        while i<5 :
            if i>0:
                type_key = "field"+str(i)+"_type"
                value_key = "field"+str(i)+"_value"
                opt_key = "field"+str(i)+""
            if type_key and value_key in params:
                field_type = params[type_key]
                value  = str(params[value_key])
                opt = default_mod[identifier]
                if opt_key in params:
                    opt = str(params[opt_key])
                if field_type and value and not value=="":
                    entry_key= str(opt+'_'+field_type)
                    add_to_dict(params,entry_key,value)
                    #params[entry_key] = value
                    #para_map = update_para_map(para_map,entry_key,value)
            if type_key in params:
                del params[type_key]
            if value_key in params:
                del params[value_key]
            if opt_key in params:
                del params[opt_key]
            i += 1
        for entry_key in params:
            value = params[entry_key]
            if not value =='':
                para_map = update_para_map(para_map,entry_key,value)
        
        return None, para_map

#Parse regular sidebar         
def parse_regular_sidebar(params):
        for key in params:
            if isinstance(params[key],list):
                    params.update({key:params[key][0]})
        return None, params
        
def parse_query_language(query):        
            kw = ""

            query_list = query.split(',')
            params ={}
            for q in query_list:
                if len(q)==0:
                    pass
                elif q[0] in query_mods and not "=" in q:
                    if len(q)>1:
                        add_to_dict(params,q[0]+"keywords",q[1:])
                    #if par != "":
                    #    par += ","
                    #par += "\""+q[0]+"\":\""+q[1:]+"\""
                elif "=" in q:
                    key_value = q.split("=")
                    key = key_value[0]
                    value = key_value[1]
                    del key_value[0]
                    del key_value[0]
                    if len(key_value)>0 :
                        for v in key_value:
                            value += "+"+v
                    if value.startswith("+"):
                        del value[0]
                    while value.endswith('\\'):
                        value = value[:-1]
                    add_to_dict(params,key,value)
                    #par += "\""+key+"\":\""+value+"\""
                else:
                    if not kw=="":
                        kw += "+"
                    kw += q
            while kw.endswith('\\'):
                kw = kw[:-1]
            query = "keywords="+kw + ", params=" + json.dumps(params)
            return query



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
            if key.startswith('i_') and not key.endswith("_opt"):
                params.update({str(key[2:]):str(request.GET[key])})
        return params    

all_words_map = {
    'gallica' : 'all',
    'nga' : 'all words'
}

opt_map = {
    'and':'',
    'or':'?',
    'except':'-',
    'all':'',
    'none':'-',
    'the':'+',
    'any':'?',
    'not':'-'
    }    

opt_type_map = {
    '':'and',
    '?':'or',
    '-':'except'
    }
    
default_mod = {
    'gallica':'and',
    'trove':'all of the words',
    'digitalnz':'and'
    }
    
complex_searcher = ["gallica", "trove","digitalnz"]
