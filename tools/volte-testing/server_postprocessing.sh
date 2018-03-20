#!/bin/bash

# Authors: Antonis Gotsis, Marios Poulakis
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: Bash script for running VoLTE tests with MONROE Nodes using Android phones: Post-process caller and receiver recorded files (convert to wav, synchornize and compare quality) 

# Should run after "phone1_caller.sh" and "phone2_receiver.sh" on server e.g. 192.168.1.2
# First RUN: "mkdir $(dbus-uuidgen | head -c 8)" to create a new experiment folder and then get inside
# RUN in experiment folder: e.g. ./server_postprocessing.sh

# convert amr files to wav
ffmpeg -y -i caller.amr -f wav caller.wav
ffmpeg -y -i receiver.amr -f wav receiver.wav

# synch duration (caller file may be larger due to the delay till call is answered)
dur1=$(soxi -D receiver.wav)
dur2=$(soxi -D caller.wav)
comp=$(echo $dur1'>'$dur2 | bc -l)
if [[ $comp -eq $zero ]]; then
	echo "dur2"
	ddiff=$(echo $dur2 - $dur1 | bc)
	echo $ddiff	
	sox caller.wav caller_synched.wav trim $ddiff | bc -l
	cp receiver.wav receiver_synched.wav
else
	echo "dur1"
	ddiff=$(echo $dur1 - $dur2 | bc)
	echo $ddiff
	sox receiver.wav receiver_synched.wav trim $ddiff | bc -l
	cp caller.wav caller_synched.wav
fi

# files info
soxi $file1 | tee -a  output.txt
soxi $file2 | tee -a  output.txt
soxi receiver_synched.wav | tee -a  output.txt
soxi caller_synched.wav | tee -a  output.txt

# compare files using PESQ
./PESQ +16000 receiver_synched.wav caller_synched.wav | tail -1 | tee -a  output.txt

