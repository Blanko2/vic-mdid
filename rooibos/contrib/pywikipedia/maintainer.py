#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
A wiki-maintainer script that shares tasks between workers, requires no intervention.

This script requires the Python IRC library http://python-irclib.sourceforge.net/

Warning: experimental software, use at your own risk
"""
__version__ = '$Id: maintainer.py 5852 2008-08-27 14:44:46Z balasyum $'

# Author: Balasyum
# http://hu.wikipedia.org/wiki/User:Balasyum

from ircbot import SingleServerIRCBot
from irclib import nm_to_n
import random
import wikipedia
import thread
import threading
import time
import rciw
import censure

ver = 1

site = wikipedia.getSite()
site.forceLogin()

class rcFeeder(SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.rcbot = rciw.IWRCBot(site)
        self.tasks = []

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        pass

    def on_pubmsg(self, c, e):
        try:
            msg = unicode(e.arguments()[0],'utf-8')
        except UnicodeDecodeError:
            return
        name = msg[8:msg.find(u'14',9)]
        if 'rciw' in self.tasks:
            self.rcbot.addQueue(name)
        if 'censure' in self.tasks:
            thread.start_new_thread(censure.checkPage, (name, True))

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

    def on_quit(self, e, cmd):
        pass

class MaintcontBot(SingleServerIRCBot):
    def __init__(self, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        feederThread = threading.Thread(target=self.feederBot)
        feederThread.setDaemon(True)
        feederThread.start()

    def feederBot(self):
        self.feed = rcFeeder('#' + site.language() + '.' + site.family.name, site.loggedInAs(), "irc.wikimedia.org")
        self.feed.start()

    def on_nicknameinuse(self, c, e):
        c.nick("mainter" + str(random.randrange(100, 999)))

    def on_welcome(self, c, e):
        self.connection.privmsg("maintcont", "workerjoin " + site.language() + '.' + site.family.name + ' ' + str(ver))

    def on_privmsg(self, c, e):
        nick = nm_to_n(e.source())
        c = self.connection
        cmd = e.arguments()[0]
        do = cmd.split()
        if do[0] == "accepted":
            print "Joined the network"
            thread.start_new_thread(self.activator,())
        elif do[0] == "tasklist" and len(do) > 1:
            self.feed.tasks = do[1].split('|')

    def on_dccmsg(self, c, e):
        pass

    def on_dccchat(self, c, e):
        pass

    def activator(self):
        while True:
            self.connection.privmsg("maintcont", "active")
            time.sleep(10)

class Maintainer:
    def __init__(self):
        controllThread = threading.Thread(target=self.controllBot)
        controllThread.setDaemon(True)
        controllThread.start()
        while True:
            raw_input()

    def controllBot(self):
        bot = MaintcontBot("mainter" + str(random.randrange(100, 999)), "irc.freenode.net")
        bot.start()

if __name__ == "__main__":
    Maintainer()
