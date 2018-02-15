#!/bin/sh
iptables --table nat --flush
iptables --flush
iptables -A INPUT -s 10.0.0.0/24 -j ACCEPT
iptables -A OUTPUT -d 10.0.0.0/24 -j ACCEPT

iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
