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
import socket
import SocketServer

t = Twitter()
try:
    f = file("../../twitauth")
    twitpass = f.readline()
    f.close()
    print "DEBUG: %s" % twitpass
except Exception,e:
    print e.message

twitpass = twitpass.rstrip()
t.set_auth("noisedoor", twitpass)

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
        duration = int(time.time() - self.lastopen)
        if self.oldstate == self.OPEN:
            if duration == 1800:
                self.say_public("Door has been open for more than half an hour, close it!")
            elif duration == 600:
                self.say_public("Door has been open for more than 10 minutes.")
            elif duration == 300:
                self.say_public("Door has been open for more than 5 minutes.")

        if newstate != self.oldstate:
            self.oldstate = newstate
            if newstate == self.OPEN:
                self.lastopen = time.time()
            elif newstate == self.CLOSED:
                self.status = "Door opened for %u seconds" % duration
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

    def cmd_disktemp(self, args, e):
        f = file('temp')
        line = f.readline()
        f.close()
        self.reply(e, line)

    def cmd_lastopened(self, args, e):
        if self.lastopen > 0:
            self.reply(e, self.status + " at %s" % time.ctime(self.lastopen))

    def cmd_mdns(self, args, e):
        f = file('mdns')
        line = f.readline()
        f.close()
        self.reply(e, "mDNS workstation services I've seen lately: " + line)

#    def cmd_eval(self, args, e):
#        try:
#            self.reply(e, eval(" ".join(args)))
#        except Exception, ex:
#            self.reply(e, ex.message)
            
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

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        cur_thread = currentThread()
        response = "%d" % self.server.bot.oldstate
        self.request.send(response)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    def __init__(self, mixin, tcpserver, bot):
        self.bot = bot
        SocketServer.TCPServer.__init__(self, mixin, tcpserver)

def main():
    HOST, PORT = "", 4545

    bot = NoisedoorBot("#noisebridge-test", "noisedoor", "irc.freenode.net", 6667)
    server = ThreadedTCPServer((HOST, PORT), ThreadedTCPRequestHandler, bot)
    ip, port = server.server_address
    server_thread = Thread(target=server.serve_forever)
    server_thread.setDaemon(True)
    server_thread.start()
    print "Server loop running in thread:", server_thread.getName()
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
