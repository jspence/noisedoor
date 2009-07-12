#!/usr/bin/env python

from ircbot import SingleServerIRCBot
from twyt.twitter import Twitter, TwitterException
from threading import *
from fcntl import ioctl
from array import array
import time
import sys
import os

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

    def on_pubmsg(self, c, e):
        if e.arguments()[0].startswith(".lastopened"):
            if self.lastopen > 0:
                c.privmsg('#noisebridge', self.status + " at %s" % time.ctime(self.lastopen))

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
