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

class NoisecodeBot(SingleServerIRCBot):
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
            cmd=" ".join(args)
            forbidden=['close', 'smtp', 'url', 'http', 'socket', 'disconnect', 'irc', 'kick', 'die', 'kill', 'link', 'for', 'exec', 'while', 'eval', 'join', 'part', 'connection']
            allowed=['dr_jesus', 'schoen']
            authorized=0
            clean=0
            for word in forbidden:
                if cmd.lower().find(word) != -1:
                    break
                else:
                    clean=1

            if not clean:
                for user in allowed:
                    if nm_to_n(e.source()) == user:
                        authorized=1
                        break
                else:
                    authorized=0

            if not authorized and not clean:
                self.reply(e, "Permission denied.")
                return
            else:
                self.reply(e, eval(cmd).split("\n")[0])

        except Exception, ex:
            self.reply(e, ex.message)
            
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
    bot = NoisecodeBot("#noisebridge", "noisecode", "irc.freenode.net", 6667)
    bot.start()

if __name__ == "__main__":
    main()



#twitter() {
#	curl -u noisedoor:password -d "status=$1" http://twitter.com/statuses/update.xml
#}

#getstatus() {
#	if ./check | grep -q 5f; then
#		s=0
#	else
#		s=1
#	fi
#}

# getstatus
# os=$s
# s=$s

# while true; do
# 	getstatus
# 	if test $s != $os; then
# 		echo -n `date` >> log
# 		echo "State change detected: $os->$s"
# 		now=`date +%s`
# 		date
# 		if test $s = 1; then
# 			lastopen=`date +%s`
# 		else
# 			if test -n "$lastopen"; then
# 				duration=$(($now - $lastopen))
# 				lastopen=""
# 			fi
# 			status="Door closed"
# 			if test -n "$duration"; then
# 				status="$status (open for $duration seconds)"
# 			fi
# 			twitter "$status"
# 		fi
# 	fi
# 	if test -n "$lastopen" && test $(($lastopen + 90)) -lt "$now"; then
# 		curl -u noisedoor:password -d "status=Someone left the door open!" http://twitter.com/statuses/update.xml
# 		lastopen=""
# 	fi
# 	os=$s;
# done
