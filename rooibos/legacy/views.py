from rooibos.util.soap import SimpleSOAPView

soap = SimpleSOAPView(namespace='http://mdid.jmu.edu/webservices')

def Login(userID, password):
    return 'Logging in %s with password %s' % (userID, password)

soap.registerFunction(Login, namespace='http://mdid.jmu.edu/webservices')

