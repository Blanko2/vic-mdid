"""
Parses parameters received from DigitalNZ sidebar search
Not dealt with internally to keep consistency with other
searchers
"""

def parse_parameters(parameters):
    """ returns a dict with suitable parameters"""
    params = {}
    for p in parameters:
        params[str(p)] = str(parameters[p])
    if 'keywords' in params and params['keywords'] !={}:
        params['text']=params['keywords']
        del params['keywords'] 
    return params
        
