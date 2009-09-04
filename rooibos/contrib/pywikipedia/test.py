#!/usr/bin/python
"""
Script to perform some tests.
"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distributed under the terms of the MIT license.
#
__version__='$Id: test.py 3890 2007-07-19 21:14:10Z misza13 $'
#
import re,sys,wikipedia

for arg in wikipedia.handleArgs():
    wikipedia.output(u"Unknown argument: %s" % arg)
    wikipedia.stopme()
    sys.exit(1)

mysite = wikipedia.getSite()
if mysite.loggedInAs():
    wikipedia.output(u"You are logged in on %s as %s." % (repr(mysite), mysite.loggedInAs()))
else:
    wikipedia.output(u"You are not logged in on %s." % repr(mysite))

wikipedia.stopme()

