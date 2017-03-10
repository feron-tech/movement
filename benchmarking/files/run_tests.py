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

#-------------------------------------------------------------------------------
# configuration
#-------------------------------------------------------------------------------
# Look at specific interfaces: the list will be cross-checked with the actual interfaces detected in the system.
acceptable_ifaces       = ['eth0','op0']      # comma-separated list
# ping configuration
pingServer              = 'google.com' # IP or URL to hit
pingCount               = 5            # number of ping hits
# iperf configuration
iperfServerIPaddr       = 'iperf.volia.net'         # IP or URL where iperf3 server resides
iperfServerfPort        = 5201                      # port where iperf3 server listens
iperfTimeToRun          = 5                         # time duration of iperf3 test
# speedtest configuration
speedtestServer     = 'http://speedtest.otenet.gr' #IP or URL where Speedtest Server is Hosted
# curl configuration
curlTimeout             = 5                                                                 # duration of file transfer
# curl HTTP-GET specific
curlRemoteFile          = 'http://releases.ubuntu.com/14.04/ubuntu-14.04.5-desktop-amd64.iso' # remote file location for HTTP GET
# curl HTTP-POST specific
curlLocalFile           = "/opt/monroe/jellyfish-15-mbps-hd-h264.mkv"                       # local file location for HTTP POST
curlServerResponseURL   = "http://52.174.152.255/cgi-bin/save_file.py"                      # server-side file upload app
curlUsername            = "testuser"                                                        # authentication username for file upload
curlPassword            = "testuser"                                                        # authentication passworkd for file upload
# metadata related
zmqport                 = "tcp://172.17.0.1:5556"                               # where to listen
metadata_topic          = "" # empty string stands for all messages             # subscribe to all messages
topic_filters           = ["MONROE.META.DEVICE.MODEM","MONROE.META.DEVICE.GPS"] # filter out unwanted
# filenames to store results
dataResultsFilename     = 'dataResultsFile.json'                                # file to store data results
metadataResultsFilename = 'metadataResultsFile.json'                            # file to store metadata results
# logging
logfilename         = 'experimentLogFile.txt'

#-------------------------------------------------------------------------------
# load local modules
#------------------------------------------------------------------------------
# import tests functionality
from tests import ping_test, iperf3_test, speedtest_test, curl_test
# import metadata functionality
from metadata import retrieve_metadata_thread

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
fileHandler = logging.FileHandler(os.path.join(os.path.expanduser('~'), logfilename))
logger.addHandler(fileHandler)


#-------------------------------------------------------------------------------
# main program
#-------------------------------------------------------------------------------

# initialization
experimentConfig = {
"nodeid": "-1",
"start" : 0,
"stop"  : 0
}

# determine if i am running locally or within docker: if in docker store results in /monroe/results else at home dir.
inDocker = bool(re.search('docker', subprocess.check_output(['cat', '/proc/1/cgroup'],shell=False)))
if inDocker:
    logging.info("I am running within docker")
else:
    logging.info("I am running in standalone mode (outside docker)")

try: # read configuration from node: this is feasible when we run the experiment through the scheduler, and not locally.
    with open('/monroe/config') as configfd:
        experimentConfig.update(json.load(configfd)) # experimentConfig fields are updated with real values
except Exception as e: # no configuration file, go on with dummy initialization done above
    logging.info('[Handled Exception] There is no configuration file: we run in local mode.')
    # do nothing

# setting experiment
logging.info(("Starting measurement procedure  for nodeid = {}").format(experimentConfig['nodeid']))
# Starting and ending scheduled times are valid for experiments run through scheduler. For local experiments these are irrelevant.
logging.info(("Testing Scheduled to start at                : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(experimentConfig['start']))))
logging.info(("Testing Scheduled not to end later than      : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(experimentConfig['stop']))))
# Read time from local clock
logging.info(("Current date/time is                         : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))))

# network setup identification
detected_ifaces = netifaces.interfaces()
active_ifaces = sorted(list(set(acceptable_ifaces) & set(detected_ifaces)))
logging.info(("Active Ifaces: {}").format(active_ifaces))

if active_ifaces:
    print('At least 1 active interface found')

    # metadata thread instantiation & start retrieving in the background
    mdThread = retrieve_metadata_thread(zmqport, metadata_topic, topic_filters, metadataResultsFilename, experimentConfig, logger)
    #mdThread = retrieve_metadata_thread()
    mdThread.setDaemon(True)
    mdThread.start()

    # begin core actions
    with open(os.path.join(os.path.expanduser('~'),'tempDataJSON.txt'), mode='w') as dataResultsFile: # dump json formatted results here
        # initialize the list to store experimental results
        expResultsList = []
        # network usage measurement dictionary
        networkUsage = {}
        for i in active_ifaces:
            networkUsage[i] = {'tx': {'before': -1, 'after': -1}, 'rx': {'before': -1, 'after': -1} }

        # start per iface testing
        for iface in active_ifaces:
            print('In Interface {}').format(iface)
            try:
                ipaddr = netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr']
                # get network usage before the experiments (in MB)
                command_line_rx = 'cat /sys/class/net/'+iface+'/statistics/tx_bytes'
                command_line_tx = 'cat /sys/class/net/'+iface+'/statistics/rx_bytes'
                networkUsage[iface]['tx']['before'] =  str(float(subprocess.check_output(command_line_tx.split(" "),shell=False))/(1000**2))
                networkUsage[iface]['rx']['before'] =  str(float(subprocess.check_output(command_line_rx.split(" "),shell=False))/(1000**2))

                # Experiments
                # get current results index
                resultRecords_old = len(expResultsList)

                # PING Experiment
                expResultsList.insert(len(expResultsList), ping_test(iface, experimentConfig, pingServer, ipaddr, pingCount, logger))
                # iperf-upload
                expResultsList.insert(len(expResultsList), iperf3_test(iface, experimentConfig, iperfServerIPaddr, iperfServerfPort, iperfTimeToRun, 'send', ipaddr, logger))
                # iperf-download
                expResultsList.insert(len(expResultsList), iperf3_test(iface, experimentConfig, iperfServerIPaddr, iperfServerfPort, iperfTimeToRun, 'receive', ipaddr, logger))
                # speedtest full test (upload, download, ping)
                expResultsList.insert(len(expResultsList), speedtest_test(iface, experimentConfig, speedtestServer, ipaddr, logger))
                # curl http download (GET)
                expResultsList.insert(len(expResultsList), curl_test(iface, experimentConfig, curlRemoteFile, ipaddr, curlTimeout, 'download', logger))
                # curl http upload (POST)
                expResultsList.insert(len(expResultsList),curl_test(iface, experimentConfig, curlLocalFile,  ipaddr, curlTimeout, 'upload', logger,curlServerResponseURL, curlUsername, curlPassword))


                # get network usage after the experiments and print to output
                networkUsage[iface]['tx']['after'] =  str(float(subprocess.check_output(command_line_tx.split(" "),shell=False))/(1000**2))
                networkUsage[iface]['rx']['after'] =  str(float(subprocess.check_output(command_line_rx.split(" "),shell=False))/(1000**2))
                logging.info(('\n\tTraffic data consumed for current experiment round: Receive {:.2f} MB / Send {:.2f} MB').format(
                    float(networkUsage[iface]['tx']['after'])-float(networkUsage[iface]['tx']['before']),
                    float(networkUsage[iface]['rx']['after'])-float(networkUsage[iface]['rx']['before'])))

                # Write last round results to file
                for m in expResultsList[resultRecords_old:len(expResultsList)]:
                    json.dump(m, dataResultsFile, sort_keys=True, indent=4, separators=(',', ': '))

            except Exception as e:
                print("Error in current Interface testing")


#-------------------------------------------------------------------------------
# finalization actions
#-------------------------------------------------------------------------------
# move result files to target dir
if active_ifaces: # at least one interface found
    if inDocker:
        shutil.copy2(os.path.join(os.path.expanduser('~'),'tempDataJSON.txt'), os.path.join('/monroe/results',dataResultsFilename))
    else:
        shutil.copy2(os.path.join(os.path.expanduser('~'),'tempDataJSON.txt'), os.path.join(os.path.expanduser('~'),dataResultsFilename))

    # terminate metadata thread & allow for some time to end thread
    mdThread.terminate()
    time.sleep(3)

logging.info('\nExit main program normally at ' + time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time())))
shutil.copy2(os.path.join(os.path.expanduser('~'),logfilename), os.path.join('/monroe/results',logfilename))
