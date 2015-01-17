from rooibos.unitedsearch.external.translator.trove_dict import query_dict
from rooibos.unitedsearch.common import *
def parse_trove_query(url, query_terms, empty_arg):
    
    
    url = url
    year_from = "*"
    year_to = "*"
    arg = empty_arg
    arg_indexes = []
    if "query_string" in query_terms:
        query_string = query_terms["query_string"]
        arg["query_string"] = query_string
        side_bar = False

        del query_terms["query_string"]
    else:
        keywords = ""
        mod_keywords = ""
        query_string = ""
        mod_quries = ""
        side_bar = True
            
            
    
    
    if "start year" in query_terms:
        year_from = str(query_terms["start year"])
        arg["start year"] = query_terms["start year"]
        if side_bar:
            if not query_string=="":
                query_string += ","
            query_string += query_dict["start year"]+"="+ year_from
        del(query_terms["start year"])
    if "end year" in query_terms:
        year_to = str(query_terms["end year"])
        arg["end year"] = query_terms["end year"]
        if side_bar:
            if not query_string=="":
                query_string += ","
            query_string += query_dict["end year"]+"="+ year_to
        del(query_terms["end year"])
    if (not year_from == "*") or (not year_to=="*"):
        date_tag = "date:["+year_from+"%20TO%20"+year_to+"]" 
    else:
        date_tag = None
    if "availability" in query_terms:
        availability = list_to_str(query_terms["availability"])
        arg["availability"] = availability
        if side_bar:
            if not query_string=="":
                query_string += ","
            query_string += query_dict["availability"]+"="+ availability
        del query_terms["availability"]
        if availability in availability_map:
            availability_tag = "&l-availability="+availability_map[availability]
        else:
            availability_tag = "&l-availability="+availability_map["Online"]
    else:
        arg["availability"] = "Online"
        availability_tag = "&l-availability="+availability_map["Online"]
    

    
    for key in query_terms:
        value_list = query_terms[key]
        if not isinstance(value_list,list):
            value_list = [value_list]
        for value in value_list:
            url_entry, arg_entry = parse_trove_index(key, value)

            url = add_index(url,url_entry)
            if arg_entry:

                if arg_entry[0] == "all of the words" or arg_entry[0] == "the phrase" and not arg_entry[1][1]=="":
                    arg_indexes.insert(0,arg_entry)
                    if side_bar and not arg_entry[1][1]=="":
                        if arg_entry[1][0] == "keywords" or arg_entry[1][0] == "keyword":
                            query_string = query_dict[arg_entry[0]]+arg_entry[1][1]+","+query_string
                        else:
                            query_string = query_dict[arg_entry[0]]+query_dict[arg_entry[1][0]]+"="+arg_entry[1][1]+","+query_string

                else:
                    arg_indexes.append(arg_entry)
                    if side_bar and not arg_entry[1][1]=="":
                        if arg_entry[1][0] == "keywords" or arg_entry[1][0] == "keyword":
                            query_string = query_dict[arg_entry[0]]+arg_entry[1][1]+","+query_string
                        else:
                            query_string = query_dict[arg_entry[0]]+query_dict[arg_entry[1][0]]+"="+arg_entry[1][1]+","+query_string
    if  date_tag:
        url = add_index(url,date_tag)
    if availability_tag:
        url += availability_tag

    url += "&s=OFFSET"
    
    
    while (",,") in query_string:   
        query_string = query_string.replace(",,",",")
    while query_string.startswith(','):
        query_string = query_string[1:]
    while query_string.endswith(','):
        query_string = query_string[:-1]
    if not "query_string" in arg:
        arg["query_string"] = query_string
    

    while len(arg_indexes)<5:
        arg_indexes.append([])
    arg["field"] = arg_indexes

    return url , arg

def parse_trove_index(key, value):
    index = key
    mod = "all of the words"
    if "_" in index:
        mod_index = index.split("_")
        mod = mod_index[0]
        index = mod_index[1]
    if mod == "all of the words":
        return parse_all_index(index,value)
    elif mod == "any of the words":
        return parse_any_index(index,value)
    elif mod == "the phrase":
        return parse_phrase_index(index,value)
    elif mod == "none of the words":
        return parse_none_index(index,value)
    else:
        return parse_all_index(index,value)
    

def parse_all_index(index, value):
    value = check_value(value)
    if value == "":
        return "",None
    url_entry = index_header(index)+"("+value.replace(' ','%20')+")"
    arg_entry = ["all of the words",[index,value]]
    return url_entry, arg_entry

def parse_any_index(index, value):
    value = check_value(value)
    if value == "":
        return "",None
    url_entry = index_header(index)+"("+value.replace(' ',"%20OR%20")+")"
    arg_entry = ["any of the words",[index,value]]
    return url_entry, arg_entry

def parse_phrase_index(index, value):
    if value == "":
        return "",None
    url_entry = index_header(index)+'\"'+value.replace(' ','%20')+'\"'
    arg_entry = ["the phrase",[index,value]]
    return url_entry, arg_entry

def parse_none_index(index, value):
    if value == "":
        return "",None
    url_entry = '-'+index_header(index)+'('+value.replace(' ','%20')+')'
    arg_entry = ["none of the words",[index,value]]
    return url_entry, arg_entry

def check_value(value):
    return value

def index_header(index):
    if index=="keyword":
        return ""
    else:
        return index+":"


def add_index(url, url_entry):
    if url_entry == "":
        return url
    if url.endswith("q="):
        url += url_entry
    else:
        url += "%20"+url_entry
    return url

availability_map = { 
    "Online":"y", 
    "Access conditions":"y%2Fr", 
    "Freely available":"y%2Ff"
}

