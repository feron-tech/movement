#!/usr/bin/python

# Authors: Antonis Gotsis, Marios Poulakis, Demetrios Vassiliadis (Feron Technologies P.C.)
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: A high-level python script for configuring & running multiple network test experiments. Tested with python2

# for main program (data tests)
import netifaces   # needed for detecting network interfaces
import subprocess  # needed for calling external shell commands
import shutil      # needed for copying files to /monroe/results/dir
import json        # needed for processing/storing formated results
import os          # needed for getting files metadata
import time        # needed for managing time
import sys         # needed for debugging purposes
import re          # needed for string search procedures
import uuid        # needed for generating a unique id for JSON recording
from pprint import pprint # needed for pretty printing json
import logging     # needed for logging useful info
# for metadata retrieval
import zmq         # needed for retrieving metadata from daemon
import threading   # needed for running metadata retrieval as thread within the main program
# for database access
from pymongo        import MongoClient      # needed for writting results to database
from pprint         import pprint           # needed for pretty printing list results
from urllib         import quote_plus       # needed for connecting to the mongo db (python2). for python3 use: <from urllib.parse import quote_plus>
from pymongo.errors import OperationFailure # needed for db connection checking



#-------------------------------------------------------------------------------
# function measuring networking usage
#-------------------------------------------------------------------------------
def getNetworkUsage(interface):
	results = []
	command_line_rx = 'cat /sys/class/net/'+interface+'/statistics/tx_bytes'
	command_line_tx = 'cat /sys/class/net/'+interface+'/statistics/rx_bytes'
	results.append(str(float(subprocess.check_output(command_line_tx.split(" "),shell=False))/(1000**2)))
	results.append(str(float(subprocess.check_output(command_line_rx.split(" "),shell=False))/(1000**2)))
	return results

#-------------------------------------------------------------------------------
# add appropriate routing roule for current iface
#-------------------------------------------------------------------------------
def setRouting(ip_address, ip_rules_preconf, prio, action='ADD'):

	# flush cache to empty the cache
	command_line = "ip route flush cache"
	output = subprocess.check_output(command_line.split(" "),shell=False)

	# get lookup table index for current iface
	lookup_table_ind = []
	#iface_lookups = []
	for i in ip_rules_preconf:
		if re.split(':',(re.split('\t',i))[0])[0]=="10000":
			#iface_lookups.append(re.split('\t',i)[1])
			current_ip_rule = re.split(' ',re.split('\t',i)[1])
			if ip_address in current_ip_rule:
				lookup_table_ind = current_ip_rule[3]
				#logger.info("For current IP (" + ip_address + "), the lookup table index is: " + lookup_table_ind)
				break

	# add temp rule for routing global traffic
	if lookup_table_ind:
		if action == 'ADD':
			command_line = "ip rule add from all iif lo lookup " + str(lookup_table_ind) + " pref " + str(prio)
		elif action == 'DEL':
			command_line = "ip rule del from all iif lo lookup " + str(lookup_table_ind) + " pref " + str(prio)
		try:
			output = subprocess.check_output(command_line.split(" "),shell=False)
		except Exception as e:
			logger.info(("ip rule add exception: {}").format(str(e)))

	# flush cache to empty the cache
	command_line = "ip route flush cache"
	output = subprocess.check_output(command_line.split(" "),shell=False)

	# print current ip tables rules
	command_line = "ip ru"
	try:
		output = subprocess.check_output(command_line.split(" "),shell=False)
		logger.info(" ****************** ip ru command output current ******************")
		logger.info(("{}").format(str(output)))
	except Exception as e:
		logger.info(("exception error in ip ru command {}").format(str(e)))

	#command_line = "ip -s route get 147.102.25.88"
	#output = subprocess.check_output(command_line.split(" "),shell=False)
	#logger.info(("IP ROUTE GET: {}").format(str(output)))


#-------------------------------------------------------------------------------
# load configuration
#-------------------------------------------------------------------------------
import config_local as cfg

#-------------------------------------------------------------------------------
# load local modules
#------------------------------------------------------------------------------
# import tests functionality
from tests import ping_test, iperf3_test, speedtest_test, curl_test, video_streaming_probe_test
# import metadata functionality
from metadata import retrieve_metadata_thread
# video streaming probe functionality
from video.video_streaming_probe import VideoStreamingProbe

#-------------------------------------------------------------------------------
# setup a logger
#-------------------------------------------------------------------------------
# create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
 # create console handler and set level to info
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setLevel(logging.INFO)
formatter = logging.Formatter("%(message)s") #formatter = logging.Formatter("[%(levelname)s] %(message)s")
consoleHandler.setFormatter(formatter)
logger.addHandler(consoleHandler)
# add file handler in addition to console handler
fileHandler = logging.FileHandler(os.path.join('/monroe/results', cfg.temp_logfilename))
logger.addHandler(fileHandler)


#-------------------------------------------------------------------------------
# main program
#-------------------------------------------------------------------------------

# initialization
experimentConfig = {
"nodeid": "-1",
"start" : 0,
"stop"  : 0,
"experimentid": 0
}

# determine if i am running locally or within docker: if in docker store results in /monroe/results else at home dir.
inDocker = bool(re.search('docker', subprocess.check_output(['cat', '/proc/1/cgroup'],shell=False)))
if inDocker:
	logging.info("I am running within docker")
else:
	logging.info("I am running in standalone mode (outside docker)")


try: # read configuration from node: this is feasible when we run the experiment through the scheduler, and not locally.
	with open('/monroe/results/nodeid') as nodeidfd:
		experimentConfig['nodeid'] = nodeidfd.readline().rstrip()
except Exception as e: # no configuration file, go on with dummy initialization done above
	logging.info('[Handled Exception] There is no nodeid file: we run through scheduler.')
	# do nothing

try: # read configuration from node: this is feasible when we run the experiment through the scheduler, and not locally.
	with open('/monroe/config') as configfd:
		experimentConfig.update(json.load(configfd)) # experimentConfig fields are updated with real values
except Exception as e: # no configuration file, go on with dummy initialization done above
	logging.info('[Handled Exception] There is no configuration file: we run in local mode.')
	# do nothing

#create a unique id for the current experiment
experimentConfig["experimentid"] = str(uuid.uuid4())[:8]  # smaller thatn 'str(uuid.uuid1())'

# setting experiment
logging.info(("Starting measurement procedure  for nodeid = {}").format(experimentConfig['nodeid']))
# Starting and ending scheduled times are valid for experiments run through scheduler. For local experiments these are irrelevant.
logging.info(("Testing Scheduled to start at                : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(experimentConfig['start']))))
logging.info(("Testing Scheduled not to end later than      : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(experimentConfig['stop']))))
# Read time from local clock
logging.info(("Current date/time is                         : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))))

# network setup identification
detected_ifaces = netifaces.interfaces()
active_ifaces = sorted(list(set(cfg.acceptable_ifaces) & set(detected_ifaces)))
logging.info(("Active Ifaces: {}").format(active_ifaces))

if active_ifaces:
	print('At least 1 active interface found')

	# get all INET ifaces Gateways
	gws = netifaces.gateways()
	gws_INET = gws[netifaces.AF_INET]
	logging.info(('NetIfaces GWs: {}').format(gws_INET))

	# thread activation
	if cfg.metadataActivateFlag:
		# metadata thread instantiation & start retrieving in the background
		mdThread = retrieve_metadata_thread(cfg.zmqport, cfg.metadata_topic, cfg.topic_filters, cfg.temp_metadataResultsFilename, cfg.metadataResultsFilename, experimentConfig, logger)
		#mdThread = retrieve_metadata_thread()
		mdThread.setDaemon(False)
		mdThread.start()

	# database connection initialization
	if cfg.storeToDb:
		client = MongoClient("mongodb://%s:%s@%s:%s/%s" % (quote_plus(cfg.dbuser), quote_plus(cfg.dbpassword), cfg.dbhost, cfg.dbport, cfg.dbname))
		try:
			# The ismaster command is cheap and does not require auth.
			client[cfg.dbname].command('ismaster')
		except OperationFailure:
			print(" \nConnection to DATABASE failed")
			sys.exit('Exit program normally at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
		db = client[cfg.dbname] # define db or create db if not exists
		measdata = db[cfg.dbCollectionName] # define collection or create collection if not exists
		print("\nConnection to DB Ok. There are {} measurement data records in DB.\n").format(measdata.count())

	# begin core actions
	with open(os.path.join('/monroe/results',cfg.temp_dataResultsFilename), mode='w') as dataResultsFile: # dump json formatted results here
		# initialize the list to store experimental results
		expResultsList = []
		dataResultsFile.write("[")
		# network usage measurement dictionary
		networkUsage = {}
		for i in active_ifaces:
			networkUsage[i] = {'tx': {'before': -1, 'after': -1}, 'rx': {'before': -1, 'after': -1} }

		# get preconfigured ip rules
		ip_rules_all = []
		command_line = "ip ru"
		try:
			output = subprocess.check_output(command_line.split(" "),shell=False)
			logger.info("ip ru command output:")
			logger.info(("{}").format(str(output)))
			ip_rules_all = re.split('\n',output)
		except Exception as e:
			logger.info(("exception error in ip ru command {}").format(str(e)))

		# start measurement rounds
		for roundix in range(1,cfg.Nrounds+1):
			# start round
			logging.info(('///// Round {}/{} /////').format(roundix,cfg.Nrounds))
			# start per iface testing
			for iface in active_ifaces:
				logging.info(('In Interface {}').format(iface))
				try:
					ipaddr = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']

					# apply ip route
					setRouting(ipaddr, ip_rules_all, 15000, 'ADD')

					# get network usage before the experiments (in MB)
					for xiface in active_ifaces:
						networkUsage[xiface]['tx']['before'] = getNetworkUsage(xiface)[0]
						networkUsage[xiface]['rx']['before'] = getNetworkUsage(xiface)[1]

					# Experiments
					# get current results index
					resultRecords_old = len(expResultsList)

					# PING Experiment
					expResultsList.insert(len(expResultsList), ping_test(iface, experimentConfig, cfg.pingServer, ipaddr, cfg.pingCount, logger, bindToIface=True))
					#expResultsList.insert(len(expResultsList), ping_test(iface, experimentConfig, cfg.pingServer, ipaddr, cfg.pingCount, logger, bindToIface=False))
					# iperf-upload
					expResultsList.insert(len(expResultsList), iperf3_test(iface, experimentConfig, cfg.iperfServerIPaddr, cfg.iperfServerfPort, cfg.iperfTimeToRun, 'send', ipaddr, logger, bindToIface=True))
					#expResultsList.insert(len(expResultsList), iperf3_test(iface, experimentConfig, cfg.iperfServerIPaddr, cfg.iperfServerfPort, cfg.iperfTimeToRun, 'send', ipaddr, logger, bindToIface=False))
					# iperf-download
					expResultsList.insert(len(expResultsList), iperf3_test(iface, experimentConfig, cfg.iperfServerIPaddr, cfg.iperfServerfPort, cfg.iperfTimeToRun, 'receive', ipaddr, logger, bindToIface=True))
					#expResultsList.insert(len(expResultsList), iperf3_test(iface, experimentConfig, cfg.iperfServerIPaddr, cfg.iperfServerfPort, cfg.iperfTimeToRun, 'receive', ipaddr, logger, bindToIface=False))
					# speedtest full test (upload, download, ping)
					expResultsList.insert(len(expResultsList), speedtest_test(iface, experimentConfig, cfg.speedtestServer, ipaddr, logger, bindToIface=True))
					#expResultsList.insert(len(expResultsList), speedtest_test(iface, experimentConfig, cfg.speedtestServer, ipaddr, logger, bindToIface=False))
					# curl http download (GET)
					expResultsList.insert(len(expResultsList), curl_test(iface, experimentConfig, cfg.curlRemoteFile, ipaddr, cfg.curlTimeout, 'download', logger, bindToIface=True))
					#expResultsList.insert(len(expResultsList), curl_test(iface, experimentConfig, cfg.curlRemoteFile, ipaddr, cfg.curlTimeout, 'download', logger, bindToIface=False))
					# curl http upload (POST)
					expResultsList.insert(len(expResultsList), curl_test(iface, experimentConfig, cfg.curlLocalFile,  ipaddr, cfg.curlTimeout, 'upload', logger, cfg.curlServerResponseURL, cfg.curlUsername, cfg.curlPassword, bindToIface=True))
					#expResultsList.insert(len(expResultsList), curl_test(iface, experimentConfig, cfg.curlLocalFile,  ipaddr, cfg.curlTimeout, 'upload', logger, cfg.curlServerResponseURL, cfg.curlUsername, cfg.curlPassword, bindToIface=False))
					# video streaming experiment
					expResultsList.insert(len(expResultsList),video_streaming_probe_test( iface, experimentConfig, ipaddr, cfg.vp_args, cfg.vp_youtube_url, cfg.vp_timeout, VideoStreamingProbe,  logger))

					# get network usage after the experiments and print to output the consumed MBs
					logging.info('\n')
					for xiface in active_ifaces:
						networkUsage[xiface]['tx']['after'] = getNetworkUsage(xiface)[0]
						networkUsage[xiface]['rx']['after'] = getNetworkUsage(xiface)[1]
						logging.info(('\tIface: {} - Traffic data consumed for current experiment round: Receive {:.2f} MB / Send {:.2f} MB').format(xiface,
							float(networkUsage[xiface]['tx']['after'])-float(networkUsage[xiface]['tx']['before']),
							float(networkUsage[xiface]['rx']['after'])-float(networkUsage[xiface]['rx']['before'])))

					# delete ip route
					setRouting(ipaddr, ip_rules_all, 15000, 'DEL')

					# Write last round results to file
					for m in expResultsList[resultRecords_old:len(expResultsList)]:
						json.dump(m, dataResultsFile, sort_keys=True, indent=4, separators=(',', ': '))
						dataResultsFile.write(",\n")

					# Write last round results to database
					if cfg.storeToDb:
						try:
							measdata.insert_many(expResultsList[resultRecords_old:len(expResultsList)])
							print("[INFO] There are {} measurement data records in DB.\n").format(measdata.count())
						except Exception as e:
							print ('Exception in Database Insert procedure: ' + str(e))

				except Exception as e:
					print e
					print("Error in current Interface testing")

		# before closing file
		dataResultsFile.seek(-2, os.SEEK_END)
		dataResultsFile.truncate()
		dataResultsFile.write("]")

#-------------------------------------------------------------------------------
# finalization actions
#-------------------------------------------------------------------------------
now_str = time.strftime("%Y%m%d-%H%M%S_", time.gmtime(time.time()))
# move result files to target dir
if active_ifaces: # at least one interface found
	shutil.copy2(os.path.join('/monroe/results',cfg.temp_dataResultsFilename), os.path.join('/monroe/results',cfg.dataResultsFilename+"_"+experimentConfig["experimentid"]+".json"))

	# terminate metadata thread & allow for some time to end thread
	if cfg.metadataActivateFlag:
		logging.info('\nSent termination command to metadata thread  ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
		mdThread.terminate()
		#time.sleep(5)

command_line = "ip route flush cache"
output = subprocess.check_output(command_line.split(" "),shell=False)
logging.info('\nEnded main program normally at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
shutil.copy2(os.path.join('/monroe/results',cfg.temp_logfilename), os.path.join('/monroe/results',cfg.logfilename+"_"+experimentConfig["experimentid"]+".txt"))
