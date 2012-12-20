from . import empty_dict, artstor_dict, nga_dict, gallica_dict, trove_dict, ngaust_dict, digitalnz_dict, local_dict
from  rooibos.unitedsearch.common import break_query_string 
import urllib
class Query_Language:
    """
    The definition of the Universal Query Language for Vic-Mdid
     
    all dictionaries need a 'keywords' equivalent and the 
    query language written here can compensate for any added
    keys that are not present in other dictionaries
    ie: if a key exists in one dict but not another, this class
    will put the values into 'keywords' for the searcher that doesnt
    have it. 
    
    Generally this class will be instantiated and then have searcher_translator 
    invoked with a given query
    
    returns - a translated dictionary for the specified searcher 
        keys that are not in the specified searcher are sent to that 
        searcher's 'keyword' value 
    """
    searcher_identity='default'
    searcher_dictionary = empty_dict.dictionary

    """ query mods are the modifiers for the passed keys. 
        '-' = without,
        '+' = and/exact phrase,
        '?' = or"""
    query_mods=[
        '-',
        '+',
        '?',
    ]
    """ if a searcher has a key that needs to be included -
    it does not fit spec with a pre-existing key - then add it 
    here """
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
	""" requires the searcher identifier to select the correct dict"""
        self.searcher_identity = searcher_id

    def searcher_translator(self, query):
        """ Translates the given universal query into parameters accepted by the searchers
            returns a translated dictionary
        """ 
        self.searcher_dictionary = self.searcher_to_dict(self.searcher_identity)
        keywords, params = break_query_string(query) 
        print "params after breaking"+str(params)
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
            'ngaust' : ngaust_dict.dictionary,
            'local' : local_dict.dictionary
        }.get(searcher_identity, empty_dict.dictionary)
       
    def _check_valid(self, parameters):
        """ 
        Checks if all parameters in the query are valid, if not, they go into 'keywords' 
            
        method compensates for values that are present in some searchers but not others
        will not search for a without modifier attached to keywords at the moment
        """
        keywords=""
        del_list = []
        add_list = []
        for p in parameters:
            if p not in self.query_lang and not p[0] in self.query_mods:
                keywords += str(parameters[p])
                del_list.append(p)
            elif p[0] in self.query_mods and len(p)>0:
                if self.searcher_identity == "nga":
                    new_key = p[0]
                    add_list.append([new_key,parameters[p]])
                    del_list.append(p)
                elif p[1:] not in self.query_lang:
                    keywords += str(parameters[p])
                    del_list.append(p)
        for p in del_list:
            if p in parameters:
                del parameters[p]
        for p in add_list:
            parameters[self._translate(p[0])] = p[1]
        return keywords     

    def _translate_words(self, parameters):
        """ breaks the params and sends them to _translate"""
        translated_dictionary={}
        for word in parameters:
            print "word = "+word
            translated_word = word
            modifier = None
            for mod in self.query_mods:
                if word.startswith(mod):
                    modifier = self._translate(mod)
                    print modifier
                    translated_word = word[len(mod):]
            translated_word = modifier+"_"+self._translate(translated_word) if modifier else self._translate(translated_word) 
            print "translated_word ======="+translated_word
            translated_dictionary[translated_word] = str(parameters[word]) 
        return translated_dictionary

    def _translate(self, word):
        """ performs the actual translation of the given word"""
        return self.searcher_dictionary[str(word)] if str(word) in self.searcher_dictionary else self.searcher_dictionary['keywords'] 
        
