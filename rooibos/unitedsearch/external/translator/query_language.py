import rooibos.unitedsearch.external.translator 
import rooibos.unitedseach.common

"""
generating language for the vic-MDID query language
"""

query_lang=[
    'keywords',
    'creator',
    'title',
    'start date',
    'end date']


def searcher_translator(query_string, searcher_identity):
    #translate between the query_lang and the 
    # searcher dictionary
    
    #use searcher id to get the correct dictionary 
    query_string, params = common.break_query_string(query_string) 
    searcher_dictionary = searcher_to_dict(searcher_identity)
    params = ""
    keywords = "" 
    searcher_query = "q=keywords:"+keywords+", params:"+params
    return searcher_query


"""
returns the searcher_dictionary equivalent to the 
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
   
def translate(searcher_dict):
    #do the actual translation
    #create a new dictionary and populate 
    # it with the values received from the 
    # query string
