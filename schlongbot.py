#!/usr/bin/env python

from irclib import irc_lower,nm_to_n
from ircbot import SingleServerIRCBot
from threading import *
from fcntl import ioctl
from array import array
import time
import sys
import os
import string
import socket
import SocketServer
import sys
import types
import lxml
import lxml.html
import lxml.etree
import urllib
import random

class SchlongBot(SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def reply(self, e, text):
        if e.eventtype() == "pubmsg":
            self.say_public("%s: %s" % (nm_to_n(e.source()), text))
        else:
            self.say_private(nm_to_n(e.source()), text)

    def say_public(self, text):
        "Print TEXT into public channel, for all to see."
        for chname, chobj in self.channels.items():
            self.connection.privmsg(self.channel, text)

    def cmd_eval(self, args, e):
        try:
                rep = "schlong " + e.arguments()[0]
        except Exception, ex:
		rep = str(ex)
	finally:
	        self.reply(e, rep)

    def searchfor(self, c, e, key):
        doc = lxml.html.parse('http://chan4chan.com/archive/search/' + key)
        results = filter(lambda x: x.get('href').find('http://img.chan4chan.com/', 0) != -1, doc.xpath('//a'))
        self.reply(e, random.choice(results).get('href'))

    def on_pubmsg(self, c, e):
        if nm_to_n(e.source()).find("noise") != -1:
            return
        a = string.split(e.arguments()[0], ":", 1)
        if len(a) > 1 and irc_lower(a[0]) == irc_lower(c.get_nickname()):
            self.do_command(e, string.strip(a[1]))
            return

        keywordmap=[['schlong', 'penis'],
                    ['goatse', 'goatse'],
                    ['cornholio', 'goatse']]
        results=filter(lambda x: e.arguments()[0].find(x[0]) != -1, keywordmap)
        if bool(results):
            self.searchfor(c, e, results[0][1])
            return

    def on_privmsg(self, c, e):
        if nm_to_n(e.source()) == "NickServ":
            password = file('identpass').readline().strip()
            self.reply(e, "identify %s" % password)

    def cmd_help(self, args, e):
        cmds = [i[4:] for i in dir(self) if i.startswith('cmd_')]
        self.reply(e, "Valid commands: '%s'" % "', '".join(cmds))

    def do_command(self, e, cmd):
        cmds = cmd.strip().split(" ")
        try:
            cmd_handler = getattr(self, "cmd_" + cmds[0])
        except AttributeError:
            cmd_handler = None
        if cmd_handler:
            cmd_handler(cmds[1:], e)
            return

        self.reply(e, "I don't understand '%s'."%(cmd))

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

def main():
    bot = SchlongBot("#noisebridge", "schlongbot", "irc.freenode.net", 6667)
    bot.start()

if __name__ == "__main__":
    main()
