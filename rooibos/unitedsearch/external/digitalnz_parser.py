def parse_parameters(parameters):
    """ receives a dict. """
    print 'DIGITALNZ PARSER '
    params = {}
    for p in parameters:
        params[str(p)] = str(parameters[p])
 
    return params
        
