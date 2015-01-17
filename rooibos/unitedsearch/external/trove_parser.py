
def parse_trove_query(url, query_terms, empty_arg):
    url = url
    year_from = "*"
    year_to = "*"
    arg = empty_arg
    arg_indexes = []
    if "start year" in query_terms:
        year_from = str(query_terms["start year"])
        arg["start year"] = query_terms["start year"]
        del(query_terms["start year"])
    if "end year" in query_terms:
        year_to = str(query_terms["end year"])
        arg["end year"] = query_terms["end year"]
        del(query_terms["end year"])
    if (not year_from == "*") or (not year_to=="*"):
        date_tag = "date:["+year_from+"%20TO%20"+year_to+"]" 
    else:
        date_tag = None
    if "availability" in query_terms and not query_terms["availability"] == "All":
        availability = query_terms["availability"]
        arg["availability"] = availability
        del query_terms["availability"]
        availability_tag = "&l-availability="+availability_map[availability]
    else:
        if "availability" in query_terms:
            del query_terms["availability"]
        arg["availability"] = "All"
        availability_tag = None
    for key in query_terms:
        value = query_terms[key]
        url_entry, arg_entry = parse_trove_index(key, value)
        url = add_index(url,url_entry)
        if arg_entry:
            if arg_entry[0] == "all of the words" or arg_entry[0] == "the phrase" and not arg_entry[1][1]=="":
                arg_indexes.insert(0,arg_entry)
            else:
                arg_indexes.append(arg_entry)
    if  date_tag:
        url = add_index(url,date_tag)
    if availability_tag:
        url += availability_tag
    url += "&s=OFFSET"
    while len(arg_indexes)<5:
        arg_indexes.append([])
    arg["field"] = arg_indexes
    print "trove url = "+ url
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
        print "unknown modifier"
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
    while value.startswith(' '):
        if len(value)==1:
            return ""
        value = value[1:]
    while value.endswith(' '):
        if len(value)==1:
            return ""
        value = value[-1]
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

