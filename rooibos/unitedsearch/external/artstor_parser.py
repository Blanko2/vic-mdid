""" Parses the values received from the sidebar parameters -
    this can be quite complicated when using modifiers """

def parse_parameters(parameters):
    """receives a dict"""
    print 'Artstor Parser'
    params = {}
    for p in parameters:
        params[str(p)] = str(parameters[p])
    return params 
