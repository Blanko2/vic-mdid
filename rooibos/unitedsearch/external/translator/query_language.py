import rooibos.unitedsearch.external.translator 
import rooibos.unitedseach.common

"""
generating language for the vic-MDID query language
"""
searcher_identity='default'

query_lang=[
    '-',
    '+',
    '?',
    'keywords',
    'creator',
    'title',
    'start date',
    'end date',
    'year',
    'decade',
    'century'
    ]

def searcher_translator(self, query, searcher_identity):
    self.searcher_identity = searcher_identity 
    #use searcher id to get the correct dictionary 
    keywords, params = common.break_query_string(query) 
    #need to check if params contains values such as '+/?/-creator'
    keywords += _check_valid(params)
    searcher_dictionary = searcher_to_dict(searcher_identity)
    translated_dictionary = _translate(keywords, parameters, searcher_dictionary)
    return translated_dictionary 

"""
Returns the searcher_dictionary equivalent to the 
searcher received
"""
def searcher_to_dict(searcher_identity):
    return {
        'gallica' : translator.gallica_dict,
        'nga' : translator.nga_dict,
        'digitalnz' : translator.digitalnz_dict,
        'artstor' : translator.artstor_dict,
        'trove' : translator.trove_dict
    }.get(searcher_identity, translator.empty_dict)
   
def _translate(self, keywords, parameters, searcher_dict):
    translated_dictionary={} 
    translated_keywords = searcher_dict['keywords'] 
    if keywords:
        translated_dictionary[translated_keywords] = keywords 
    for key in parameters:
        key_value = parameters[key]
        translated_key = searcher_dict[key]
        translated_dict[translated_key] = key_value
    return translated_dict 
"""
+ and - and ? not implemented
NGA does not have an or
"""
def _check_valid(parameters):
    keywords=""
    for p in parameters:
        if p not in query_lang:
            keywords+="+"parameters[p]
    return keywords     

     


