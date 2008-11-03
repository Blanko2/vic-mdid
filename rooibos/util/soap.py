""" SOAP View for Django

    This module contains blah....    
"""
#from __future__ import nested_scopes

import re
import sys
import thread
from types import *

# SOAPpy modules
from SOAPpy.version     import __version__
from SOAPpy.Parser      import parseSOAPRPC
from SOAPpy.Config      import Config
from SOAPpy.Types       import faultType, voidType, simplify
from SOAPpy.NS          import NS
from SOAPpy.SOAPBuilder import buildSOAP
from SOAPpy.Utilities   import debugHeader, debugFooter
from SOAPpy.Server      import SOAPServerBase, HeaderHandler, SOAPContext, MethodSig

try: from M2Crypto import SSL
except: pass

from django.http import HttpResponseServerError, HttpResponse

_contexts = dict()

class SimpleSOAPView(SOAPServerBase):
    def __init__(self, encoding = 'UTF-8', config = Config, namespace = None):
        
        # Test the encoding, raising an exception if it's not known
        if encoding != None:
            ''.encode(encoding)
        
        self.namespace           = namespace
        self.objmap              = {}
        self.funcmap             = {}
        self.encoding            = encoding
        self.config              = config
        
        self.allow_reuse_address = 1


    def dispatch(self, data):
        global _contexts
        try:
            (r, header, body, attrs) = \
                parseSOAPRPC(data, header = 1, body = 1, attrs = 1)
            print (r, header, body, attrs)
            method = r._name
            args   = r._aslist()
            kw     = r._asdict()
            
            if self.config.simplify_objects:
                args = simplify(args)
                kw = simplify(kw)
            
            if self.config.specialArgs: 
                ordered_args = {}
                named_args   = {}
                
                for (k,v) in  kw.items():
                    if k[0]=="v":
                        try:
                            i = int(k[1:])
                            ordered_args[i] = v
                        except ValueError:
                            named_args[str(k)] = v
                        
                    else:
                        named_args[str(k)] = v
                    
            ns = r._ns
                
            if len(self.path) > 1 and not ns:
                ns = self.path.replace("/", ":")
                if ns[0] == ":": ns = ns[1:]
                
            # authorization method
            a = None
                
            keylist = ordered_args.keys()
            keylist.sort()
                
            # create list in proper order w/o names
            tmp = map( lambda x: ordered_args[x], keylist)
            ordered_args = tmp
            
            resp = ""
            
            # For fault messages
            if ns:
                nsmethod = "%s:%s" % (ns, method)
            else:
                nsmethod = method
                        
            try:
                # First look for registered functions
                if self.funcmap.has_key(ns) and \
                    self.funcmap[ns].has_key(method):
                    f = self.funcmap[ns][method]

                    # look for the authorization method
                    if self.config.authMethod != None:
                        authmethod = self.config.authMethod
                        if self.funcmap.has_key(ns) and \
                               self.funcmap[ns].has_key(authmethod):
                            a = self.funcmap[ns][authmethod]
                else:
                    # Now look at registered objects
                    # Check for nested attributes. This works even if
                    # there are none, because the split will return
                    # [method]
                    f = self.objmap[ns]
                    
                    # Look for the authorization method
                    if self.config.authMethod != None:
                        authmethod = self.config.authMethod
                        if hasattr(f, authmethod):
                            a = getattr(f, authmethod)
                        
                    # then continue looking for the method
                    l = method.split(".")
                    for i in l:
                        f = getattr(f, i)
            except Exception, e:
                info = sys.exc_info()
                resp = buildSOAP(faultType("%s:Client" % NS.ENV_T,
                                           "Method Not Found",
                                           "%s : %s %s %s" % (nsmethod,
                                                              info[0],
                                                              info[1],
                                                              info[2])),
                                 encoding = self.encoding,
                                 config = self.config)
                del info
                #print e
                return resp
            else:
                try:
                    if header:
                        x = HeaderHandler(header, attrs)
                    
                    fr = 1
                    
                    # call context book keeping
                    # We're stuffing the method into the soapaction if there
                    # isn't one, someday, we'll set that on the client
                    # and it won't be necessary here
                    # for now we're doing both
                    
                    if "SOAPAction".lower() not in self.headers.keys() or \
                       self.headers["SOAPAction"] == "\"\"":
                        self.headers["SOAPAction"] = method
                        
                    thread_id = thread.get_ident()
                    _contexts[thread_id] = SOAPContext(header, body,
                                                       attrs, data,
                                                       None,
                                                       self.headers,
                                                       self.headers["SOAPAction"])
                    
                    # Do an authorization check
                    if a != None:
                        if not apply(a, (), {"_SOAPContext" :
                                             _contexts[thread_id] }):
                            raise faultType("%s:Server" % NS.ENV_T,
                                            "Authorization failed.",
                                            "%s" % nsmethod)
                    
                    # If it's wrapped, some special action may be needed
                    if isinstance(f, MethodSig):
                        c = None
                    
                        if f.context:  # retrieve context object
                            c = _contexts[thread_id]
                        
                        if self.config.specialArgs:
                            if c:
                                named_args["_SOAPContext"] = c
                            fr = apply(f, ordered_args, named_args)
                        elif f.keywords:
                            # This is lame, but have to de-unicode
                            # keywords
                            
                            strkw = {}
                            
                            for (k, v) in kw.items():
                                strkw[str(k)] = v
                            if c:
                                strkw["_SOAPContext"] = c
                            fr = apply(f, (), strkw)
                        elif c:
                            fr = apply(f, args, {'_SOAPContext':c})
                        else:
                            fr = apply(f, args, {})
                        
                    else:
                        if self.config.specialArgs:
                            fr = apply(f, ordered_args, named_args)
                        else:
                            fr = apply(f, args, {})
                        
                        
                    if type(fr) == type(self) and \
                        isinstance(fr, voidType):
                        resp = buildSOAP(kw = {'%sResponse' % method: fr},
                            encoding = self.encoding,
                            config = self.config)
                    else:
                        resp = buildSOAP(kw =
                            {'%sResponse' % method: {'Result': fr}},
                            encoding = self.encoding,
                            config = self.config)
                    
                    # Clean up _contexts
                    if _contexts.has_key(thread_id):
                        del _contexts[thread_id]
                    
                except Exception, e:
                    import traceback
                    info = sys.exc_info()
                    
                    if isinstance(e, faultType):
                        f = e
                    else:
                        f = faultType("%s:Server" % NS.ENV_T,
                                      "Method Failed",
                                      "%s" % nsmethod)
                        
                    if self.config.returnFaultInfo:
                        f._setDetail("".join(traceback.format_exception(
                            info[0], info[1], info[2])))
                    elif not hasattr(f, 'detail'):
                        f._setDetail("%s %s" % (info[0], info[1]))
                    del info
                    print e   
                    resp = buildSOAP(f, encoding = self.encoding,
                       config = self.config)
                    return resp
                else:
                    return resp
        except faultType, e:
            import traceback
            info = sys.exc_info()
            if self.config.returnFaultInfo:
                e._setDetail("".join(traceback.format_exception(
                        info[0], info[1], info[2])))
            elif not hasattr(e, 'detail'):
                e._setDetail("%s %s" % (info[0], info[1]))
            del info

            resp = buildSOAP(e, encoding = self.encoding,
                config = self.config)
    
    def wsdl(self):
        method = 'wsdl'
        function = namespace = None
        if self.funcmap.has_key(namespace) and self.funcmap[namespace].has_key(method):
            function = self.funcmap[namespace][method]
        else: 
            if namespace in self.objmap.keys():
                function = self.objmap[namespace]
                l = method.split(".")
                for i in l:
                    function = getattr(function, i)
                    
        if function:
            response = apply(function, ())
            return str(response)
        else:
            return 'WSDL could not be generated!'

    def __call__(self, request, path=''):
        """ SimpleXMLRPCView is callable so it can be installed as a view.

            Django calls it with 'request', which is a HttpRequest            
        """
        self.path = path
        self.headers = request.META # compatible?
        
        if request.META['REQUEST_METHOD'] == 'GET':
            if request.META['QUERY_STRING'] == 'wsdl':
                wsdl = self.wsdl()
                return HttpResponse(wsdl, mimetype='text/xml')
            else:
                return HttpResponseServerError('Use /?wsdl to get WSDL.')
        elif request.META['REQUEST_METHOD'] != 'POST':
            return HttpResponseServerError('Non POST methods not allowed.')
                
        try:
            response = self.dispatch(request.raw_post_data)
            print response
            print self.objmap, self.funcmap
        except Exception, e:
            # internal error, report as HTTP server error
            return HttpResponseServerError('internal error')
        else:
            # got a valid XML RPC response
            return HttpResponse(response, mimetype="text/xml")

