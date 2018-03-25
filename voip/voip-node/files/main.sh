#!/bin/bash

# Summary: Bash and python scripts for configuring & running VoIP tests.
# RUN with sudo

dev=$1
NODE_ID=$2
EXP_ID=$3
SERVER_IP=$4
ip=$5
round=$6

touch output.txt

# add appropriate rules per interface
rule=$(ip ru | awk -v ip="$ip" '$0~ip { print $7 }')
echo -e "\n  \033[0;31m-testing " $dev "(rule": $rule")" "\033[0m"
ip rule add from all iif lo lookup $rule pref 89999
ip route flush cache

# run voip packet sniffer in the background
python ./voip_packet_capture.py $dev $SERVER_IP 2>&1 1> voip_packet_capture.log &
ppid1=$!
#echo ${ppid1}

sleep 10 # wait for ping to be executed in voip_packet_capture.py

# run metadata sniffer in the background
python ./metadata.py $NODE_ID $EXP_ID $round 2>&1 1> /dev/null &
ppid2=$!
#echo ${ppid2}

timestamp_begin=$(date +%Y%m%d%H%M%S)

# run VoIP test (registration & call)
./voip_probe.sh $NODE_ID $EXP_ID $SERVER_IP
rc=$?
echo $rc

timestamp_end=$(date +%Y%m%d%H%M%S)

# kill metadata.py
sleep 1
pkill -f metadata.py
sleep 1
pkill -f metadata.py

# delete interface rules
ip route flush cache
ip rule del from all iif lo lookup $rule pref 89999
ip route flush cache

# check if registration and call was ok
if [ $rc -eq 0 ]; then
	# compare wav files
	curl -O http://"${SERVER_IP}"/asterisk-files/"${NODE_ID}-${EXP_ID}-out.wav" && sleep 1
	MOD1=$(stat -c %Y "${NODE_ID}-${EXP_ID}-out.wav")
	MOD2=$(stat -c %Y "${NODE_ID}-${EXP_ID}-linphone.wav")
	TDIFF=`expr $MOD1 - $MOD2`
	echo 'Files modification time difference: '$TDIFF 'sec'

	# check if server file is old
	if (( "$TDIFF" < 60 )); then
		# do PESQ comparison and get results
		(./PESQ +8000 "${NODE_ID}-${EXP_ID}-out.wav" "${NODE_ID}-${EXP_ID}-linphone.wav" | tail -1) > temp.txt
		(cat temp.txt | tee >(echo "MOS-LQO: " $(awk '{ print $8 }')) >(echo "Raw MOS: " $(awk '{ print $7 }')) | tail -2) > output.txt
		# wait for the voip_packet_capture.py
		wait ${ppid1}
		echo "aaaaaaaaaa"
		echo -e "\n"
		tail -5 voip_packet_capture.log >> output.txt
		cat output.txt
		# get results
		raw_mos=$(awk 'NF>1{print $NF}' output.txt | sed -n 1p)
		lqo_mos=$(awk 'NF>1{print $NF}' output.txt | sed -n 2p)
		packetloss=$(awk 'NF>1{print $NF}' output.txt | sed -n 3p)
		latency=$(awk 'NF>1{print $NF}' output.txt | sed -n 4p)
		jitter=$(awk 'NF>1{print $NF}' output.txt | sed -n 5p)
		r=$(awk 'NF>1{print $NF}' output.txt | sed -n 6p)
		e_mos=$(awk 'NF>1{print $NF}' output.txt | sed -n 7p)

		echo '{"experiment_id": "'"${EXP_ID}"'", "nodeid": "'"${NODE_ID}"'", "iface": "'"${dev}"'", "app": "voip", "timestamp_begin": "'"${timestamp_begin}"'", "timestamp_end": "'"${timestamp_end}"'", "results": "{"raw_mos":"'"${raw_mos}"'", "lqo_mos":"'"${lqo_mos}"'", "packetloss":"'"${packetloss}"'", "latency":"'"${latency}"'", "jitter":"'"${jitter}"'", "r":"'"${r}"'", "e_mos":"'"${e_mos}"'"}"}' > dataResultsFile_${EXP_ID}_${round}.json

	else
		 echo 'Error: Not right files' | tee output.txt
		 echo '{"experiment_id": "'"${EXP_ID}"'", "nodeid": "'"${NODE_ID}"'", "iface": "'"${dev}"'", "app": "voip", "timestamp_begin": "'"${timestamp_begin}"'", "timestamp_end": "'"${timestamp_end}"'", "status": "Failed", "exception_error":"Not right files"}' > dataResultsFile_${EXP_ID}_${round}.json
	fi

else
		echo 'Error: No registration!' | tee output.txt
		echo '{"experiment_id": "'"${EXP_ID}"'", "nodeid": "'"${NODE_ID}"'", "iface": "'"${dev}"'", "app": "voip", "timestamp_begin": "'"${timestamp_begin}"'", "timestamp_end": "'"${timestamp_end}"'", "status": "Failed", "exception_error":"No registration"}' > dataResultsFile_${EXP_ID}_${round}.json
		pkill -9 -f voip_packet_capture.py
fi

# manage results files
sleep 1
mkdir -p $EXP_ID/$dev
mkdir -p /monroe/results/${NODE_ID}_${EXP_ID}/$dev
bash -c 'cat "'"${NODE_ID}"'"-"'"${EXP_ID}"'"-linphone.wav > "'"${NODE_ID}"'"-"'"${EXP_ID}"'"-"'"${round}"'"-node.wav'
rm "${NODE_ID}-${EXP_ID}-linphone.wav"
bash -c 'cat "'"${NODE_ID}"'"-"'"${EXP_ID}"'"-out.wav > "'"${NODE_ID}"'"-"'"${EXP_ID}"'"-"'"${round}"'"-server.wav'
rm "${NODE_ID}-${EXP_ID}-out.wav"
mv -t $EXP_ID/$dev "dataResultsFile_${EXP_ID}_${round}.json" "metadataResultsFile_${EXP_ID}_${round}.json" "${NODE_ID}-${EXP_ID}-${round}-server.wav" "${NODE_ID}-${EXP_ID}-${round}-node.wav"
rm temp_metadataResultsFile output.txt temp.txt voip_packet_capture.log temp.pcap pesq_results.txt
cp -a $EXP_ID/$dev/* /monroe/results/${NODE_ID}_${EXP_ID}/$dev
