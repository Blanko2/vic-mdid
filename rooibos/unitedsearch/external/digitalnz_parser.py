def parse_parameters(parameters):
    """ receives a dict. """
    print 'DIGITALNZ PARSER '
    params = {}
    for p in parameters:
        params[str(p)] = str(parameters[p])
    if 'keywords' in params and params['keywords'] !={}:
        params['text']=params['keywords']
        del params['keywords'] 
    return params
        
