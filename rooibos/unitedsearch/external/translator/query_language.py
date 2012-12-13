import rooibos.unitedsearch.external.translator 
import rooibos.unitedseach.common

"""
generating language for the vic-MDID query language
"""
searcher_identity='default'
searcher_dictionary=translator.empty_dict

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
    'century'
    ]

def searcher_translator(self, query, searcher_identity):
    self.searcher_identity = searcher_identity 
    self.searcher_dictionary = searcher_to_dict(searcher_identity)
    keywords, params = common.break_query_string(query) 
    #need to check if params contains values such as '+/?/-creator'
    keywords += _check_valid(params)
    params = _translate_words(params)
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
   
"""
+ and - and ? not implemented
NGA does not have an or
"""
def _check_valid(self, parameters):
    keywords=""
    for p in parameters:
        if p not in self.query_lang and p != '-':
            keywords+="+"parameters[p]
    return keywords     

def _translate_words(self, parameters):
    translated_dictionary={}
    for word in parameters:
        translated_word = word
        for mod in self.query_mods:
            if word.startswith(mod):
                modifier = _translate(mod)
                translated_word = word[len(mod):]
        translated_word = modifier+_translate(translated_word) if modifier else _translate(translated_word)   
        translated_dictionary[translated_word] = parameters[word] 
    return translated_dictionary

def _translate(self, word):
    return searcher_dictionary[word] 
        
