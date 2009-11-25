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
import MySQLdb
import sys
import types
import _mysql_exceptions

class NoisesqlBot(SingleServerIRCBot):
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
	    	db = MySQLdb.connect(host="localhost", user="noisesql", db="noisesql")
            	cmd=" ".join(args)
		c = db.cursor()
		c.execute(cmd)
		o = c.fetchall()
		if type(o) == types.NoneType:
			rep=str(o)
		else:
			if len(o) == 1:
				if len(o[0]) == 1:
					rep = o[0][0]
				else:
					rep = o[0]
			else:
				rep=str(o)

	except _mysql_exceptions.ProgrammingError, ex:
        	rep = ex[1]
        except Exception, ex:
		rep = str(ex)
	finally:
	        self.reply(e, rep)

    def on_pubmsg(self, c, e):
        if nm_to_n(e.source()).find("noise") != -1:
            return
        a = string.split(e.arguments()[0], ":", 1)
        if len(a) > 1 and irc_lower(a[0]) == irc_lower(c.get_nickname()):
            self.do_command(e, string.strip(a[1]))

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
    bot = NoisesqlBot("#noisebridge", "noisesql", "irc.freenode.net", 6667)
    bot.start()

if __name__ == "__main__":
    main()
