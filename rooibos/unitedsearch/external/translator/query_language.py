from . import empty_dict, artstor_dict, nga_dict, gallica_dict, trove_dict, ngaust_dict, digitalnz_dict 
from  rooibos.unitedsearch.common import break_query_string 
import urllib
class Query_Language:
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
        'rights',
        'school',
        'accession number',
        'medium',
        'access',
        'start year',
        'end year',
        "subject",
        "language",
        "isbn",
        "issn",
        "tag"
        ]
    
    def __init__(self, searcher_id):
        self.searcher_identity = searcher_id

    def searcher_translator(self, query):
        """ Translates the given universal query into parameters accepted by the searchers""" 
        self.searcher_dictionary = self.searcher_to_dict(self.searcher_identity)
        keywords, params = break_query_string(query) 
        #need to check if params contains values such as '+/?/-creator'
        keywords += self._check_valid(params)
        translated_dictionary = self._translate_words(params)
        k = self._translate('keywords')
        if not keywords=="" :
            keywords = translated_dictionary[k]+keywords if 'keywords' in translated_dictionary else keywords
            translated_dictionary[k] = str(keywords)
        return translated_dictionary 

    def searcher_to_dict(self, searcher_identity):
        """
        Returns the searcher_dictionary equivalent to the 
        searcher received
        """
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
    def _check_valid(self, parameters):
        keywords=""
        for p in parameters:
            if p not in self.query_lang and p != '-' and p[0] != '-':
                keywords += str(parameters[p])
                del parameters[p]
        return keywords     

    def _translate_words(self, parameters):
        translated_dictionary={}
        for word in parameters:
            translated_word = word
            modifier = None
            for mod in self.query_mods:
                if word.startswith(mod):
                    modifier = self._translate(mod)
                    translated_word = word[len(mod):]
            translated_word = modifier+"_"+self._translate(translated_word) if modifier else self._translate(translated_word)   
            translated_dictionary[translated_word] = str(parameters[word]) 
        return translated_dictionary

    def _translate(self, word):
        """ can be a string or  unicode -- does casting to check for the values"""
        return self.searcher_dictionary[str(word)] if str(word) in self.searcher_dictionary else self.searcher_dictionary['keywords'] 
        
