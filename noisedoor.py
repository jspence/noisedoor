#!/usr/bin/env python

from irclib import irc_lower,nm_to_n
from ircbot import SingleServerIRCBot
from twyt.twitter import Twitter, TwitterException
from threading import *
from fcntl import ioctl
from array import array
import time
import sys
import os
import string

t = Twitter()
t.set_auth("noisedoor", "password")

class NoisedoorBot(SingleServerIRCBot):
    LPGETSTATUS = 0x060b
    OPEN = 1
    CLOSED = 0
    oldstate = CLOSED
    lastopen = 0.0
    status = ""

    def __init__(self, channel, nickname, server, port=6667):
        SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel
        self.checkDoor()

    def checkDoor(self):
        newstate = self.getDoorBit()
        if newstate != self.oldstate:
            self.oldstate = newstate
            if newstate == self.OPEN:
                self.lastopen = time.time()
            elif newstate == self.CLOSED:
                duration = time.time() - self.lastopen
                self.status = "Door opened for %u seconds" % int(duration)
                print "%s" % self.status
                #self.connection.privmsg('#noisebridge', self.status)
                try:
                    t.status_update(self.status)
                except TwitterException, e:
                    print "Problem with twitter: " + e.message

        self.t = Timer(1.0, self.checkDoor)
        self.t.start()

    def getDoorBit(self):
        f = file("/dev/lp0")
        buf = array('i', [0])
        ioctl(f.fileno(), self.LPGETSTATUS, buf, 1)
        if buf[0] == 0x5f:
            ret = self.CLOSED
        else:
            ret = self.OPEN
        f.close()
        return ret


    def reply(self, e, text):
        if e.eventtype() == "pubmsg":
            self.say_public("%s: %s" % (nm_to_n(e.source()), text))
        else:
            self.say_private(nm_to_n(e.source()), text)

    def say_public(self, text):
        "Print TEXT into public channel, for all to see."
        for chname, chobj in self.channels.items():
            self.connection.privmsg(self.channel, text)

    def cmd_lastopened(self, args, e):
        if self.lastopen > 0:
            self.reply(e, self.status + " at %s" % time.ctime(self.lastopen))

    def cmd_mdns(self, args, e):
        f = file('mdns')
        line = f.readline()
        f.close()
        self.reply(e, "mDNS workstation services I've seen lately: " + line)
        
    def on_pubmsg(self, c, e):
        a = string.split(e.arguments()[0], ":", 1)
        if len(a) > 1 and irc_lower(a[0]) == irc_lower(c.get_nickname()):
            self.do_command(e, string.strip(a[1]))

    def cmd_loadavg(self, args, e):
        self.reply(e, "Load: %.2f %.2f %.2f" % os.getloadavg())

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
    bot = NoisedoorBot("#noisebridge", "noisedoor", "irc.freenode.net", 6667)
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
