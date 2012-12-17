from . import empty_dict, artstor_dict, nga_dict, gallica_dict, trove_dict, ngaust_dict 
import rooibos.unitedsearch.common

"""
generating language for the vic-MDID query language
"""
searcher_identity='default'
searcher_dictionary = empty_dict.dictionary

query_mods=[
    '-',
    '+',
    '?',
]
query_lang=[
    'keywords',
    'creator',
    'title',
    'start date',
    'end date',
    'year',
    'decade',
    'century',
    'rights'
    ]

def searcher_translator(query, searcher_id):
    searcher_identity = searcher_id
    searcher_dictionary = searcher_to_dict(searcher_id)
    keywords, params = common.break_query_string(query) 
    #need to check if params contains values such as '+/?/-creator'
    keywords += _check_valid(params)
    translated_dictonary = _translate_words(params)
    return translated_dictionary 

"""
Returns the searcher_dictionary equivalent to the 
searcher received
"""
def searcher_to_dict(searcher_identity):
    return {
        'gallica' : gallica_dict.dictionary,
        'nga' : nga_dict.dictionary,
        'digitalnz' : digitalnz_dict.dictionary,
        'artstor' : artstor_dict.dictionary,
        'trove' : trove_dict.dictionary,
        'ngaust' : ngaust_dict.dictionary
    }.get(searcher_identity, empty_dict.dictionary)
   
"""
NGA does not have an or
"""
def _check_valid(parameters):
    keywords=""
    for p in parameters:
        if p not in query_lang and p != '-' and p[0] != '-':
            keywords += parameters[p]
    return keywords     

def _translate_words(parameters):
    translated_dictionary={}
    for word in parameters:
        translated_word = word
        for mod in query_mods:
            if word.startswith(mod):
                modifier = _translate(mod)
                translated_word = word[len(mod):]
        translated_word = modifier+"_"+_translate(translated_word) if modifier else _translate(translated_word)   
        translated_dictionary[translated_word] = parameters[word] 
    return translated_dictionary

def _translate(word):
    return searcher_dictionary[word] if searcher_dictionary[word] else searcher_dictionary['keywords'] 
    
    
