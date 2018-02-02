#!/bin/bash

# Authors: Antonis Gotsis, Marios Poulakis, Demetrios Vassiliadis (Feron Technologies P.C.)
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: Bash script for configuring & running VoIP tests.

# RUN with sudo: e.g. sudo ./run_main.sh

filepath=$(dirname "$(readlink -f "$0")")
cd $filepath

#=========== INPUT =========================
SERVER_IP="*.*.*.*"  # VoIP server
NROUNDS=2 # number of rounds
#=========== INPUT =========================

available_interf=($(ls /sys/class/net)) # find available interfaces
acceptable_interf=( eth0 usb0 op0 wwan0 usb1 op1 wwan1 usb2 op2 wwan2 wlan0 ) # array of acceptable interfaces
NODE_ID=$(cat /etc/nodeid) || NODE_ID=$(cat /nodeid) || NODE_ID="111" # get node ID
EXP_ID=$(dbus-uuidgen | head -c 8) # random experiment ID

echo "experiment ID: " $EXP_ID
echo "available interfaces: " ${available_interf[@]}
echo "acceptable interfaces: " ${acceptable_interf[@]}

for ((round=1; round <= $NROUNDS; round++))
do
	echo -e "\033[0;31m* Round "  $round "/" $NROUNDS "\033[0m"
	for dev in "${acceptable_interf[@]}"
	do
		if [[ " ${available_interf[@]} " =~ " ${dev} " ]]; then
				ip=$(/sbin/ip -o -4 addr list $dev | awk '{print $4}' | cut -d/ -f1)
				# run main for each interface with IP
				if [[ ! -z "$ip" ]] ; then
					./main.sh $dev $NODE_ID $EXP_ID $SERVER_IP $ip $round
				fi
		fi
	done
done
