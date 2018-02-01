#!/bin/bash

# RUN with sudo: e.g. sudo ./main.sh eth0 111 12345678

# capture interface
#dev='eth0'
#NODE_ID='111'
#EXP_ID='12345678'
dev=$1
NODE_ID=$2
EXP_ID=$3
SERVER_IP=$4
ip=$5
rule=$6

rule=$(ip ru | awk -v ip="$ip" '$0~ip { print $7 }')
echo $dev: $rule
ip rule add from all iif lo lookup $rule pref 89999
ip route flush cache


#echo 'Capturing ' $dev
#rm voip_packet_capture.log
#rm captureLogFile.log
#rm output.txt
touch output.txt

timestamp_begin=$(date +%Y%m%d%H%M%S)

#echo capturing $dev
python ./voip_packet_capture.py $dev $SERVER_IP 2>&1 1> voip_packet_capture.log &
#sudo python packet_sniffer_stripped.py $dev 2>&1 &
ppid1=$!
#echo ${ppid1}

sleep 10 # to execute ping
python ./metadata.py $NODE_ID $EXP_ID 2>&1 1> /dev/null &
ppid2=$!
#echo ${ppid2}

./voip_probe.sh $NODE_ID $EXP_ID $SERVER_IP
rc=$?
echo $rc

timestamp_end=$(date +%Y%m%d%H%M%S)
#kill ${ppid2}
#kill ${ppid2}
sleep 1
pkill -f metadata.py
sleep 1
pkill -f metadata.py

ip route flush cache
ip rule del from all iif lo lookup $rule pref 89999
ip route flush cache

if [ $rc -eq 0 ]; then
	# compare wav files
	curl -O http://"${SERVER_IP}"/asterisk-files/"${NODE_ID}-${EXP_ID}-out.wav" && sleep 1

	MOD1=$(stat -c %Y "${NODE_ID}-${EXP_ID}-out.wav")
	MOD2=$(stat -c %Y "${NODE_ID}-${EXP_ID}-linphone.wav")
	TDIFF=`expr $MOD1 - $MOD2`
	echo 'Files modification time difference: '$TDIFF 'sec'

	if (( "$TDIFF" < 60 )); then
		#soxi "${NODE_ID}-${EXP_ID}-out.wav"
		#soxi "${NODE_ID}-${EXP_ID}-linphone.wav"
		(./PESQ +8000 "${NODE_ID}-${EXP_ID}-out.wav" "${NODE_ID}-${EXP_ID}-linphone.wav" | tail -1) > temp.txt
		(cat temp.txt | tee >(echo "MOS-LQO: " $(awk '{ print $8 }')) >(echo "Raw MOS: " $(awk '{ print $7 }')) | tail -2) > output.txt
		wait ${ppid1}
		echo -e "\n"
		tail -5 voip_packet_capture.log >> output.txt
		cat output.txt
		raw_mos=$(awk 'NF>1{print $NF}' output.txt | sed -n 1p)
		lqo_mos=$(awk 'NF>1{print $NF}' output.txt | sed -n 2p)
		packetloss=$(awk 'NF>1{print $NF}' output.txt | sed -n 3p)
		latency=$(awk 'NF>1{print $NF}' output.txt | sed -n 4p)
		jitter=$(awk 'NF>1{print $NF}' output.txt | sed -n 5p)
		r=$(awk 'NF>1{print $NF}' output.txt | sed -n 6p)
		e_mos=$(awk 'NF>1{print $NF}' output.txt | sed -n 7p)

		echo '{"experiment_id": "'"${EXP_ID}"'", "nodeid": "'"${NODE_ID}"'", "iface": "'"${dev}"'", "app": "voip", "timestamp_begin": "'"${timestamp_begin}"'", "timestamp_end": "'"${timestamp_end}"'", "results": "{"raw_mos":"'"${raw_mos}"'", "lqo_mos":"'"${lqo_mos}"'", "packetloss":"'"${packetloss}"'", "latency":"'"${latency}"'", "jitter":"'"${jitter}"'", "r":"'"${r}"'", "e_mos":"'"${e_mos}"'"}"}' > dataResultsFile_${EXP_ID}.json

	else
		 echo 'Error: Not right files' | tee output.txt
		 echo '{"experiment_id": "'"${EXP_ID}"'", "nodeid": "'"${NODE_ID}"'", "iface": "'"${dev}"'", "app": "voip", "timestamp_begin": "'"${timestamp_begin}"'", "timestamp_end": "'"${timestamp_end}"'", "status": "Failed", "exception_error":"Not right files"}' > dataResultsFile_${EXP_ID}.json
	fi

else
		echo 'Error: No registration!' | tee output.txt
		echo '{"experiment_id": "'"${EXP_ID}"'", "nodeid": "'"${NODE_ID}"'", "iface": "'"${dev}"'", "app": "voip", "timestamp_begin": "'"${timestamp_begin}"'", "timestamp_end": "'"${timestamp_end}"'", "status": "Failed", "exception_error":"No registration"}' > dataResultsFile_${EXP_ID}.json
		pkill -9 -f voip_packet_capture.py
fi

#cat output.txt
sleep 1
mkdir -p $EXP_ID/$dev
mkdir -p /monroe/results/${NODE_ID}_${EXP_ID}/$dev
mv -t $EXP_ID/$dev "dataResultsFile_${EXP_ID}.json" "metadataResultsFile_${EXP_ID}.json" "${NODE_ID}-${EXP_ID}-out.wav" "${NODE_ID}-${EXP_ID}-linphone.wav"
rm temp_metadataResultsFile output.txt temp.txt voip_packet_capture.log temp.pcap pesq_results.txt
cp -a $EXP_ID/$dev/* /monroe/results/${NODE_ID}_${EXP_ID}/$dev

#pkill -9 -f voip_packet_capture.py
#pkill -f metadata.py
#pkill -f metadata.py

#sudo kill -9 ${ppid1}
#sudo pkill -9 -f voip_packet_capture.py # kill handled in voip_packet_capture.py
