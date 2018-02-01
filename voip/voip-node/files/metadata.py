#!/usr/bin/python

# Authors: Antonis Gotsis, Marios Poulakis, Demetrios Vassiliadis (Feron Technologies P.C.)
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: A high-level python script for configuring & running multiple network test experiments. Tested with python2


import subprocess, json,sys
import multiprocessing
import os, ast, getopt, shutil, re, subprocess
import logging     # needed for logging useful info
import zmq         # needed for retrieving metadata from daemon
import signal, time


stop=0

metadataResultsFilename = 'metadataResultsFile'                            # file to store metadata results
temp_metadataResultsFilename = 'temp_metadataResultsFile'                  # file to store (temp) metadata results
inDocker = bool(re.search('docker', subprocess.check_output(['cat', '/proc/1/cgroup'],shell=False)))

print 'inDocker: ' + str(inDocker)

#-------------------------------------------------------------------------------
# metadata zeromq
#-------------------------------------------------------------------------------
#metadataActivateFlag    = True
zmqport                 = "tcp://localhost:5556"                               # where to listen (for local)
if inDocker:
	zmqport                 = "tcp://172.17.0.1:5556"                               # where to listen (for MONROE)
metadata_topic          = "" # empty string stands for all messages             # subscribe to all messages
topic_filters           = ["MONROE.META.DEVICE.MODEM","MONROE.META.DEVICE.GPS"] # filter out unwanted

#-------------------------------------------------------------------------------
# test functions definition
#-------------------------------------------------------------------------------

# metadata results
def metadata_exp():
	global stop
	print "start metadata"
	# dump json formatted results here
	#try:
	with open(temp_metadataResultsFilename, mode='w') as metadataFile:
		metadataFile.write("[")
		# metadata.metadata_exp(zmqport, metadata_topic, topic_filters, metadataFile, experimentConfig, experimentid, logger)
		# Attach to the ZeroMQ socket as a subscriber and start listen to MONROE messages
		context = zmq.Context()
		socket = context.socket(zmq.SUB)
		socket.connect(zmqport)
		socket.setsockopt(zmq.SUBSCRIBE, metadata_topic)
		# recv timeout msec
		poller = zmq.Poller()
		poller.register(socket, zmq.POLLIN)
		# list to store captured messages
		msgList = []
		# read until stop event is sent by main program
		while stop==0:
			#print(running_proc[0][1])
			try:
				evts = poller.poll(10000)
				(topic, msgdata) = socket.recv(zmq.NOBLOCK).split(' ', 1)
				#print(topic)
			except:
				#print ("Error: Invalid zmq msg")
				continue
			# parse messages
			if any( t == 'True' for t in [str(topic.startswith(m)) for m in topic_filters] ): # filter out
				#print ('Checked Topic   : ' + topic)
				# process message
				msg = json.loads(msgdata)
				#pprint(msg)
				# add uuid and nodeid fields
				msg['experiment_id'] = sys.argv[2]
				msg['nodeid'] = sys.argv[1]
				# insert to list
				msgList.insert(len(msgList),msg)
				#print("Metadata List contains {} msgs").format(len(msgList))
				json.dump(msgList[-1], metadataFile, sort_keys=True, indent=4, separators=(',', ': '))
				metadataFile.write(",\n")
			#else:
				# print ('Irrelevant Topic: ' + topic)
				# do nothing and move on
	#except (KeyboardInterrupt, SystemExit):
	#except:
	#	print "bbbbbb"

def signal_handler(signal, frame):
	global stop
	stop=1
	#print('You pressed Ctrl+C!')
	print('stop metadata') # two ctrl+c signals are needed
	#time.sleep(2)
	shutil.copy2(temp_metadataResultsFilename, metadataResultsFilename + '_' + sys.argv[2] + '.json')
	with open(metadataResultsFilename + '_' + sys.argv[2] + '.json', mode='a') as metadataFile:
		if metadataFile.tell() > 2:
			metadataFile.seek(-2, os.SEEK_END)
			metadataFile.truncate()
		metadataFile.write("]")
	sys.exit()


if __name__=='__main__':
	#signal.signal(signal.SIGINT, signal_handler)
	signal.signal(signal.SIGTERM, signal_handler)
	metadata_exp()
	signal.pause()
