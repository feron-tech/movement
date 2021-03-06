#!/bin/bash

# Authors: Antonis Gotsis, Marios Poulakis
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: Bash script for running VoLTE tests with MONROE Nodes using Android phones: Upload recorded file and measurements (should run after call has been finished)
# Tested on OnePlus 3T with Android 7.1.1 Nougat, connected to Amarisoft LTE network

# RUN: e.g. sudo ./phone2_receiver.sh 192.168.1.2 d71cf751

SERVER_IP=$1 # post-processing server
EXP_ID=$2 # exteriment ID
echo "experiment ID: " $EXP_ID
mkdir $EXP_ID
cd $EXP_ID

# "CallHandler.apk" is running both on phone1 and on phone2 recording calls in "amr-wb" format in addition with autoanswer function that should be enabled
# pull recorded file and signal strength measurements
lastfile_amr=$(adb shell ls -td /storage/emulated/0/VoLTEtests/*.amr | head -1)
sudo adb pull $lastfile_amr .
lastlocalfile_amr=$(ls -td *.amr | head -1)
mv $lastlocalfile_amr receiver.amr
lastfile_txt=$(adb shell ls -td /storage/emulated/0/VoLTEtests/*.txt | head -1)
sudo adb pull $lastfile_txt .
lastlocalfile_txt=$(ls -td *.txt | head -1)
mv $lastlocalfile_txt receiver.txt

# upload files to server for post-processing (experiment folder should exist)
scp receiver.amr receiver.txt $SERVER_IP:/home/user/Documents/results/$EXP_ID

