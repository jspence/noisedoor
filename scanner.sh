#!/bin/sh
# scanner -- scan for people and dump data to a file

SCANNER_DIR=.

scan_mdns() {
   for host in `avahi-browse _workstation._tcp -t -p | cut -d\; -f4`; do 
       echo $host | sed -e 's/\\.*$//' | egrep -v '(pony|goat|zebra|voltron|noisebridge-greet|hippo)'
   done | xargs echo > $SCANNER_DIR/mdns
 
}

scan_bluetooth() {
    hcitool scan > $SCANNER_DIR/bluetooth
}

scan_IPs() {
    nmap -T5 -sP -oG $SCANNER_DIR/ips 172.30.0.16-254 >/dev/null 2>&1
}
while true; do
    scan_mdns
    scan_bluetooth
    scan_IPs
    sleep 60
done