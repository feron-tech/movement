#!/bin/bash
# ------ PARAMETERS -----#

filepath=$(dirname "$(readlink -f "$0")")

NODE_ID=$1
EXP_ID=$2
SERVER_IP=$3
SERVER_PORT="11880"

socket=/tmp/linphonec-$(id -u)

# REGISTER
call_extension=$(curl -s -X POST --header 'Content-Type: application/json' -d '{ "experimentId":"'"${EXP_ID}"'", "nodeId":"'"${NODE_ID}"'" }' http://${SERVER_IP}:${SERVER_PORT}/voip-registration-api/1.0.0/experiments)
call_extension=$(echo ${call_extension} | sed 's/"//g')
echo "call_extension:" ${call_extension}

# Set calling number
number="${call_extension}@${SERVER_IP}"
echo "number:" $number

# MAKE LINPHONE RC FILE
sed -e "s/SERVERIP/${SERVER_IP}/" -e "s/NODEID/${NODE_ID}/" ./linphonerc_template > ./linphonerc

# START LINPHONE
#rm *.wav # should remove previous because it will be appended
linphonec -c ./linphonerc --pipe 2>&1 |
(
while read -r line
do
		echo $line
		case $line in
				*Registration\ on\ *\ successful. )
						sleep 1
						echo ">>> initializing"
						sleep 1
						echo -n "soundcard use files" | nc -q 5 -U $socket
						sleep 1
						echo -n "record ${call_extension}-linphone.wav" | nc -q 5 -U $socket
						sleep 1
						echo -n "call ${number}" | nc -q 5 -U $socket
						#for command in "soundcard use files" "record $filename" "call $number"
						#do
						#    echo -n $command | nc -q 5 -U $socket
						#done
						;;
				*Call\ *\ with\ *\ connected. )
						sleep 1
						echo ">>> sending pass"
						#echo -n "play $passfile" | nc -q 5 -U $socket
						;;
				*Call\ terminated. )
						sleep 1
						echo ">>> quitting"
						while echo -n quit | nc -q 5 -U $socket 2&> /dev/null
						do
								i=$(expr $i + 1)
								if test $i -ge 5
								then
										echo $(basename $0): could not shut down linphonec &>2
										exit 1
								fi
								sleep 2
						done
						echo ">>> END"
						exit
						;;
				*Registration\ on\ *\ failed* )
						sleep 1
						echo ">>> quitting"
						while echo -n quit | nc -q 5 -U $socket 2&>-
						do
								i=$(expr $i + 1)
								if test $i -ge 5
								then
										echo $(basename $0): could not shut down linphonec &>2
										exit 1
								fi
								sleep 2
						done
						echo ">>> END"
						exit 1
						;;
		esac
done;
)
#echo $?;
#if [ $? == 1 ]; then
#	exit 1
#fi;
