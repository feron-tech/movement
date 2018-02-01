#!/bin/bash

# RUN with sudo: e.g. sudo ./run_main.sh

filepath=$(dirname "$(readlink -f "$0")")
cd $filepath

# Input
SERVER_IP="*.*.*.*"

# initializations - overwritten at later stage
dev="eth0"
NODE_ID="111"
EXP_ID="12345678"

available_interf=($(ls /sys/class/net))
acceptable_interf=( eth0 usb0 op0 wwan0 usb1 op1 wwan1 usb2 op2 wwan2 wlan0 )
#NODE_ID=$(cat /etc/nodeid) # if you do not work inside a MONROE node you need to explicitly pass the nodeid
EXP_ID=$(dbus-uuidgen | head -c 8)

echo "experiment ID: " $EXP_ID
echo "available interfaces: " ${available_interf[@]}
echo "acceptable interfaces: " ${acceptable_interf[@]}

for dev in "${acceptable_interf[@]}"
do
	if [[ " ${available_interf[@]} " =~ " ${dev} " ]]; then
			ip=$(/sbin/ip -o -4 addr list $dev | awk '{print $4}' | cut -d/ -f1)
			if [[ ! -z "$ip" ]] ; then
				echo "-testing " $dev
				./main.sh $dev $NODE_ID $EXP_ID $SERVER_IP $ip $rule
			fi
	fi
done
