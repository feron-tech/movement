# Authors: Antonis Gotsis (Feron Technologies P.C.)
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: A class implementing metadata retrieval and storage in the background of the main program (thread)
# Inspired by MONROE Metadata Retrieval Code

import threading   # needed for running metadata retrieval as thread within the main program
import zmq         # needed for retrieving metadata from daemon
import time        # needed for managing time
import shutil      # needed for copying files to /monroe/results/dir
import json        # needed for processing/storing formated results
import os          # needed for getting files metadata
import re          # needed for string search procedures
import uuid        # needed for generating a unique id for JSON recording
import sys         # needed for debugging purposes
import re          # needed for string search procedures
import logging     # needed for logging useful info


class retrieve_metadata_thread(threading.Thread):
	def __init__(self, zmqport, metadata_topic, topic_filters, temp_metadataResultsFilename, metadataResultsFilename, experimentConfig, logger, name='MetadataThread'):
		self._stopevent = threading.Event()
		threading.Thread.__init__(self, name=name)
		# set parameters
		self.zmqport = zmqport
		self.metadata_topic = metadata_topic
		self.topic_filters = topic_filters
		self.temp_metadataResultsFilename = temp_metadataResultsFilename
		self.metadataResultsFilename = metadataResultsFilename
		self.experimentConfig = experimentConfig
		self.logger = logger

	def terminate(self):
		 self._stopevent.set()

	def run(self):
		self.logger.info('Started metadata thread at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
		# Attach to the ZeroMQ socket as a subscriber and start listen to
		# MONROE messages
		context = zmq.Context()
		socket = context.socket(zmq.SUB)
		socket.connect(self.zmqport)
		socket.setsockopt(zmq.SUBSCRIBE, self.metadata_topic)
		# list to store captured messages
		msgList = []
		# dump json formatted results here
		with open(os.path.join('/monroe/results',self.temp_metadataResultsFilename), mode='w') as metadataFile:
			metadataFile.write("[")
			# read until stop event is sent by main program
			while not self._stopevent.isSet():
				# read message
				try:
					(topic, msgdata) = socket.recv().split(' ', 1)
				except:
					print ("Error: Invalid zmq msg")
					continue
				# parse messages
				if any( t == 'True' for t in [str(topic.startswith(m)) for m in self.topic_filters] ): # filter out
					#print ('Checked Topic   : ' + topic)
					# process message
					msg = json.loads(msgdata)
					#pprint(msg)
					# add uuid and nodeid fields
					msg['_id'] = str(uuid.uuid1())
					msg['nodeid'] = self.experimentConfig['nodeid']
					# insert to list
					msgList.insert(len(msgList),msg)
					#print("Metadata List contains {} msgs").format(len(msgList))
					json.dump(msgList[-1], metadataFile, sort_keys=True, indent=4, separators=(',', ': '))
					metadataFile.write(",\n")
				#else:
					# print ('Irrelevant Topic: ' + topic)
					# do nothing and move on
			# before closing file
			metadataFile.seek(-2, os.SEEK_END)
			metadataFile.truncate()
			metadataFile.write("]")

		# finalization actions
		now_str = time.strftime("%Y%m%d-%H%M%S_", time.gmtime(time.time()))
		shutil.copy2(os.path.join('/monroe/results',self.temp_metadataResultsFilename), os.path.join('/monroe/results',self.metadataResultsFilename+"_"+self.experimentConfig["experimentid"]+".json"))
		self.logger.info('Gracefully exit metadata retrieval thread at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
