#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
Script to log the robot in to a wiki account.

Suggestion is to make a special account to use for robot use only. Make
sure this robot account is well known on your home wikipedia before using.

Parameters:

   -all         Try to log in on all sites where a username is defined in
                user-config.py.

   -pass        Useful in combination with -all when you have accounts for
                several sites and use the same password for all of them.
                Asks you for the password, then logs in on all given sites.

   -pass:XXXX   Uses XXXX as password. Be careful if you use this
                parameter because your password will be shown on your
                screen, and will probably be saved in your command line
                history. This is NOT RECOMMENDED for use on computers
                where others have either physical or remote access.
                Use -pass instead.

   -sysop       Log in with your sysop account.

   -force       Ignores if the user is already logged in, and tries to log in.

   -v -v        Shows http requests made when logging in. This might leak
    (doubly     private data (password, session id), so make sure to check the
     verbose)   output. Using -log is recommended: this will output a lot of 
                data

If not given as parameter, the script will ask for your username and password
(password entry will be hidden), log in to your home wiki using this
combination, and store the resulting cookies (containing your password hash,
so keep it secured!) in a file in the login-data subdirectory.

All scripts in this library will be looking for this cookie file and will use the
login information if it is present.

To log out, throw away the XX-login.data file that is created in the login-data
subdirectory.
"""
#
# (C) Rob W.W. Hooft, 2003
#
# Distributed under the terms of the MIT license.
#
__version__='$Id: login.py 7145 2009-08-13 02:24:51Z alexsh $'

import re, os, query
import urllib2
import wikipedia, config

# On some wikis you are only allowed to run a bot if there is a link to
# the bot's user page in a specific list.
botList = {
    'wikipedia': {
        'en': u'Wikipedia:Registered bots',
        # Disabled because they are now using a template system which
        # we can't check with our current code.
        #'simple': u'Wikipedia:Bots',
    },
    'gentoo': {
        'en': u'Help:Bots',
    }
}


class LoginManager:
    def __init__(self, password = None, sysop = False, site = None, username=None, verbose=False):
        self.site = site or wikipedia.getSite()
        if username:
            self.username=username
            # perform writeback.
            if site.family.name not in config.usernames:
                config.usernames[site.family.name]={}
            config.usernames[site.family.name][self.site.lang]=username
        else:
            if sysop:
                try:
                    self.username = config.sysopnames[self.site.family.name][self.site.lang]
                except:
                    raise wikipedia.NoUsername(u'ERROR: Sysop username for %s:%s is undefined.\nIf you have a sysop account for that site, please add such a line to user-config.py:\n\nsysopnames[\'%s\'][\'%s\'] = \'myUsername\'' % (self.site.family.name, self.site.lang, self.site.family.name, self.site.lang))
            else:
                try:
                    self.username = config.usernames[self.site.family.name][self.site.lang]
                except:
                    raise wikipedia.NoUsername(u'ERROR: Username for %s:%s is undefined.\nIf you have an account for that site, please add such a line to user-config.py:\n\nusernames[\'%s\'][\'%s\'] = \'myUsername\'' % (self.site.family.name, self.site.lang, self.site.family.name, self.site.lang))
        self.password = password
        self.verbose = verbose
        if getattr(config, 'password_file', ''):
            self.readPassword()

    def botAllowed(self):
        """
        Checks whether the bot is listed on a specific page to comply with
        the policy on the respective wiki.
        """
        if self.site.family.name in botList and self.site.language() in botList[self.site.family.name]:
            botListPageTitle = wikipedia.translate(self.site.language(), botList)
            botListPage = wikipedia.Page(self.site, botListPageTitle)
            for linkedPage in botListPage.linkedPages():
                if linkedPage.titleWithoutNamespace() == self.username:
                    return True
            return False
        else:
            # No bot policies on other
            return True

    def getCookie(self, api = config.use_api_login, remember=True, captcha = None):
        """
        Login to the site.

        remember    Remember login (default: True)
        captchaId   A dictionary containing the captcha id and answer, if any

        Returns cookie data if succesful, None otherwise.
        """
        if api:
            predata = {
                'action': 'login',
                'lgname': self.username,
                'lgpassword': self.password,
                'lgdomain': self.site.family.ldapDomain,
            }
            address = self.site.api_address()
        else:
            predata = {
                "wpName": self.username.encode(self.site.encoding()),
                "wpPassword": self.password,
                "wpDomain": self.site.family.ldapDomain,     # VistaPrint fix
                "wpLoginattempt": "Aanmelden & Inschrijven", # dutch button label seems to work for all wikis
                "wpRemember": str(int(bool(remember))),
                "wpSkipCookieCheck": '1'
            }
            if captcha:
                predata["wpCaptchaId"] = captcha['id']
                predata["wpCaptchaWord"] = captcha['answer']
            login_address = self.site.login_address()
            address = login_address + '&action=submit'
        
        if self.site.hostname() in config.authenticate.keys():
            headers = {
                "Content-type": "application/x-www-form-urlencoded",
                "User-agent": wikipedia.useragent
            }
            data = self.site.urlEncode(predata)
            if self.verbose:
                fakepredata = predata
                fakepredata['wpPassword'] = u'XXXX'
                wikipedia.output(u"urllib2.urlopen(urllib2.Request('%s', %s, %s)):" % (self.site.protocol() + '://' + self.site.hostname() + address, self.site.urlEncode(fakepredata), headers))
            response = urllib2.urlopen(urllib2.Request(self.site.protocol() + '://' + self.site.hostname() + address, data, headers))
            data = response.read()
            if self.verbose:
                fakedata = re.sub(r"(session|Token)=..........", r"session=XXXXXXXXXX", data)
                trans = config.transliterate
                config.transliterate = False #transliteration breaks for some reason
                wikipedia.output(fakedata.decode(self.site.encoding()))
                config.transliterate = trans
            wikipedia.cj.save(wikipedia.COOKIEFILE)
            return "Ok"
        else:
            if api:
                response, data = query.GetData(predata, self.site, back_response = True)
                if data['login']['result'] != "Success":
                    faildInfo = data['login']['result']
                    #if faildInfo == "NotExists":
                    #    
                    #elif faildInfo == "WrongPass":
                    #    
                    #elif faildInfo == "Throttled":
                    #    
                    return False
            else:
                response, data = self.site.postData(address, self.site.urlEncode(predata))
                if self.verbose:
                    fakepredata = predata
                    fakepredata['wpPassword'] = fakepredata['lgpassword'] = u'XXXXX'
                    wikipedia.output(u"self.site.postData(%s, %s)" % (address, self.site.urlEncode(fakepredata)))
                    fakeresponsemsg = re.sub(r"(session|Token)=..........", r"session=XXXXXXXXXX", response.msg.__str__())
                    wikipedia.output(u"%s/%s\n%s" % (response.status, response.reason, fakeresponsemsg))
                    wikipedia.output(u"%s" % data)
            Reat=re.compile(': (.*?);')
            L = []
    
            for eat in response.msg.getallmatchingheaders('set-cookie'):
                m = Reat.search(eat)
                if m:
                    L.append(m.group(1))
    
            got_token = got_user = False
            for Ldata in L:
                if 'Token=' in Ldata:
                    got_token = True
                if 'User=' in Ldata or 'UserName=' in Ldata:
                    got_user = True
    
            if got_token and got_user:
                return "\n".join(L)
            elif not captcha:
                solve = self.site.solveCaptcha(data)
                if solve:
                    return self.getCookie(api = api, remember = remember, captcha = solve)
            return None

    def storecookiedata(self, data):
        """
        Stores cookie data.

        The argument data is the raw data, as returned by getCookie().

        Returns nothing."""
        filename = wikipedia.config.datafilepath('login-data',
                       '%s-%s-%s-login.data'
                       % (self.site.family.name, self.site.lang, self.username))
        f = open(filename, 'w')
        f.write(data)
        f.close()

    def readPassword(self):
        """
        Reads passwords from a file. DO NOT FORGET TO REMOVE READ
        ACCESS FOR OTHER USERS!!! Use chmod 600 password-file.
        All lines below should be valid Python tuples in the form
        (code, family, username, password) or (username, password)
        to set a default password for an username. Default usernames
        should occur above specific usernames.

        Example:

        ("my_username", "my_default_password")
        ("my_sysop_user", "my_sysop_password")
        ("en", "wikipedia", "my_en_user", "my_en_pass")
        """
        file = open(wikipedia.config.datafilepath(config.password_file))
        for line in file:
            if not line.strip(): continue
            entry = eval(line)
            if len(entry) == 2:   #for default userinfo
                if entry[0] == self.username: self.password = entry[1]
            elif len(entry) == 4: #for userinfo included code and family
                if entry[0] == self.site.lang and \
                  entry[1] == self.site.family.name and \
                  entry[2] == self.username:
                    self.password = entry[3]
        file.close()

    def login(self, api = config.use_api_login, retry = False):
        if not self.password:
            # As we don't want the password to appear on the screen, we set
            # password = True
            self.password = wikipedia.input(u'Password for user %s on %s:' % (self.username, self.site), password = True)

        self.password = self.password.encode(self.site.encoding())

        wikipedia.output(u"Logging in to %s as %s" % (self.site, self.username))
        try:
            cookiedata = self.getCookie(api)
        except NotImplementedError:
            wikipedia.output('API disabled because this site does not support.\nRetrying by ordinary way...')
            api = False
            return self.login(False, retry)
        if cookiedata:
            self.storecookiedata(cookiedata)
            wikipedia.output(u"Should be logged in now")
            # Show a warning according to the local bot policy
            if not self.botAllowed():
                wikipedia.output(u'*** Your username is not listed on [[%s]].\n*** Please make sure you are allowed to use the robot before actually using it!' % botList[self.site.family.name][self.site.lang])
            return True
        else:
            wikipedia.output(u"Login failed. Wrong password or CAPTCHA answer?")
            if api:
                wikipedia.output(u"API login failed, retrying using standard webpage.")
                return self.login(False, retry)
            
            if retry:
                self.password = None
                return self.login(api, True)
            else:
                return False
    
    def logout(self, api = config.use_api):
        flushCk = False
        if api and self.site.versionnumber() >= 12:
            if query.GetData({'action':'logout'}, self.site) == []:
                flushCk = True
        else:
            text = self.site.getUrl(self.site.get_address("Special:UserLogout"))
            if self.site.mediawiki_message('logouttext') in text: #confirm loggedout
                flushCk = True
        
        if flushCk:
            filename = wikipedia.config.datafilepath('login-data',
                       '%s-%s-%s-login.data' % (self.site.family.name, self.site.lang, self.username))
            try:
                os.remove(filename)
            except:
                pass
            wikipedia.output('%s is logged out.' % self.site)
            return True
        
        return False

    def showCaptchaWindow(self, url):
        pass
    
def main():
    username = password = None
    sysop = False
    logall = False
    forceLogin = False
    verbose = False
    cleanAll = clean = False

    for arg in wikipedia.handleArgs():
        if arg.startswith("-pass"):
            if len(arg) == 5:
                password = wikipedia.input(u'Password for all accounts:', password = True)
            else:
                password = arg[6:]
        elif arg == "-clean":
            clean = True
        elif arg == "-sysop":
            sysop = True
        elif arg == "-all":
            logall = True
        elif arg == "-force":
            forceLogin = True
        else:
            wikipedia.showHelp('login')
            return
    
    if wikipedia.verbose > 1:
      wikipedia.output(u"WARNING: Using -v -v on login.py might leak private data. When sharing, please double check your password is not readable and log out your bots session.")
      verbose = True # only use this verbose when running from login.py
    if logall:
        if sysop:
            namedict = config.sysopnames
        else:
            namedict = config.usernames

        for familyName in namedict.iterkeys():
            for lang in namedict[familyName].iterkeys():
                try:
                    site = wikipedia.getSite(lang, familyName)
                    loginMan = LoginManager(password, sysop = sysop, site = site, verbose=verbose)
                    if clean:
                        if os.path.exists(wikipedia.config.datafilepath('login-data',
                          '%s-%s-%s-login.data' % (familyName, lang, namedict[familyName][lang]))):
                            loginMan.logout()
                    else:
                        if not forceLogin and site.loggedInAs(sysop = sysop):
                            wikipedia.output(u'Already logged in on %s' % site)
                        else:
                            loginMan.login()
                except wikipedia.NoSuchSite:
                    wikipedia.output(lang+ u'.' + familyName + u' is not a valid site, please remove it from your config')

    else:
        if clean:
            try:
                site = wikipedia.getSite()
                lgm = LoginManager(site = site)
                lgm.logout()
            except wikipedia.NoSuchSite:
                pass
        else:
            loginMan = LoginManager(password, sysop = sysop, verbose=verbose)
            loginMan.login()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
