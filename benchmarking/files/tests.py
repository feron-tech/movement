# Authors: Antonis Gotsis (Feron Technologies P.C.)
# Date: May 2016
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: Contains the full functionality for each test. One function per test type is defined.

import time        # needed for managing time
import subprocess  # needed for calling external shell commands
import re          # needed for string search procedures
import uuid        # needed for generating a unique id for JSON recording
import json        # needed for processing/storing formated results
import sys         # needed for sys functionalities calling

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def ping_test(iface, experimentConfig, serverIPaddr, sourceIPaddr, numberOfPings, logger):
    # supports typical ping test
    command_line = "ping -c " + str(numberOfPings) + " -I " + sourceIPaddr + " " + serverIPaddr
    logger.info('\n\tRunning PING for Iface {}'.format(iface))
    try:
        tbegin = time.time()
        logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tbegin))))
        # the output is in string format
        output = subprocess.check_output(command_line.split(" "),shell=False)
        tend = time.time()
        logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tend))))

        # process ping output
        # apply re to find the summary substring pattern start
        pattern = 'min/avg/max/(m|std)dev ='
        [(m.start(0), m.end(0)) for m in re.finditer(pattern, output)]
        summaryVals_nonfin = output[m.end(0)+1:]
        # print summaryVals
        # get rid of end part and keep only the 4 values: min, avg, max, mdev
        [(m.start(0), m.end(0)) for m in re.finditer('ms\n', summaryVals_nonfin)]
        summaryVals = summaryVals_nonfin[:m.start(0)-1]
        summaryVals = summaryVals.split('/')
        summaryVals = [float(i) for i in summaryVals]
        #print results
        logger.info(('\t\tResults for {} Pings from Host {} --> Server {}').format(numberOfPings, sourceIPaddr, serverIPaddr))
        logger.info(('\t\t\tPing Average (msec) = {:.3f}').format(float(summaryVals[1])))
        logger.info(('\t\t\tPing Minimum (msec) = {:.3f}').format(float(summaryVals[0])))
        logger.info(('\t\t\tPing Maximum (msec) = {:.3f}').format(float(summaryVals[2])))
        # return values
        return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'ping', 'host': sourceIPaddr, 'server': serverIPaddr, 'conf': [numberOfPings],
        'tbegin': tbegin, 'tend': tend, 'results': {'avg': summaryVals[1], 'min': summaryVals[0], 'max': summaryVals[2]}}
    except subprocess.CalledProcessError as exc:
        #logger.info(("\tUnable to complete ping experiment. Error code:{}, Error message: {}").format(exc.returncode, str(exc)))
        return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'ping', 'host': sourceIPaddr, 'server': serverIPaddr, 'conf': [numberOfPings],
        'exception_error':str(exc)}
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def iperf3_test(iface, experimentConfig, serverIPaddr, serverPort, timeToRun, mode, sourceIPaddr, logger):
    # supports iperf3 TCP SEND/RECEIVE tests

    command_line = "iperf3 -c " + serverIPaddr + " -p " + str(serverPort) + " -B " + sourceIPaddr + " -t " + str(timeToRun) + " -J"
    # if mode is receive add -R flag
    if mode == 'send':
        logger.info(('\n\tRunning iperf3 UPLOAD for Iface {}').format(iface))
    elif mode == 'receive':
        command_line = command_line + ' -R'
        logger.info(('\n\tRunning iperf3 DOWNLOAD for Iface {}').format(iface))

    try:
        tbegin = time.time()
        logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tbegin))))
        output = subprocess.check_output(command_line.split(" "),shell=False)
        tend = time.time()
        logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tend))))
        # turn it to json format
        data = json.loads(output)
        logger.info(('\t\tResults from Host {} --> Server {}').format(data['start']['connected'][0]['local_host'],
                                        data['start']['connected'][0]['remote_host']))
        # calculate bit rate
        received_bitrate_Mbps = float(data['end']['streams'][0]['receiver']['bytes']*8/data['end']['streams'][0]['receiver']['seconds'])/(1000**2)
        sender_bitrate_Mbps   = float(data['end']['streams'][0]['sender']['bytes']*8/data['end']['streams'][0]['sender']['seconds'])/(1000**2)
        # print results
        logger.info(('\t\t\t Measured [R] Bit Rate Calc (Mbps) = {:.4f}').format(received_bitrate_Mbps))
        #print('\t Receiver Bit Rate Direct (Mbps) = {:.4f}').format(data['end']['streams'][0]['receiver']['bits_per_second']/(1000**2))
        # return values
        return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'iperf3', 'host': sourceIPaddr, 'server': serverIPaddr,
        'conf': {'mode': mode, 'timeToRun':timeToRun}, 'tbegin': tbegin, 'tend': tend,
        'results': {'received_bitrate_Mbps':received_bitrate_Mbps, 'sender_bitrate_Mbps':sender_bitrate_Mbps}}

    except Exception as exc:
        logger.info(("\tUnable to complete iperf experiment. Error message {}").format(str(exc)))
        return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'iperf3', 'host': sourceIPaddr, 'server': serverIPaddr,
        'conf': {'mode': mode, 'timeToRun':timeToRun},'exception_error':str(exc)}
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def speedtest_test(iface, experimentConfig, serverURL, sourceIPaddr, logger):
    # supports command-line speedtest using speedtest-cli
    command_line = "/opt/monroe/speedtest-cli --mini " + serverURL + " --source " + sourceIPaddr + " --json"
    logger.info(('\n\tRunning SPEEDTEST for Iface {}').format(iface))
    try:
        # execute experiment
        tbegin = time.time()
        logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tbegin))))
        output = subprocess.check_output(command_line.split(" "),shell=False)
        tend = time.time()
        logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tend))))

        # read data
        data = json.loads(output)
        downloadBitrateMbps = data['download']/(1000**2)
        uploadBitrateMbps = data['upload']/(1000**2)
        pingmsec = data['ping']
        logger.info(('\t\tResults from Host {} --> Server {}').format(sourceIPaddr, serverURL))
        logger.info(('\t\t\tDownload Bit Rate (Mbps) = {:.3f}').format(downloadBitrateMbps))
        logger.info(('\t\t\tUpload Bit Rate   (Mbps) = {:.3f}').format(uploadBitrateMbps))
        logger.info(('\t\t\tLatency           (msec) = {:.2f}').format(pingmsec))

        # return values
        return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'speedtest', 'host': sourceIPaddr, 'server': serverURL,
        'tbegin': tbegin, 'tend': tend, 'results': {'downloadBitrateMbps': downloadBitrateMbps, 'uploadBitrateMbps': uploadBitrateMbps, 'pingmsec': pingmsec}}

    except subprocess.CalledProcessError as exc:
        logger.info(("\tUnable to perform speedtest experiment. Error code:{}.  Error message: {}").format(exc.returncode, str(exc)))
        return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'speedtest', 'host': sourceIPaddr, 'server': serverURL,
        'exception_error':str(exc)}
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def curl_test(iface, experimentConfig, filename, sourceIPaddr, timeout, mode, logger, curlServerResponseURL="", curlUsername="", curlPassword=""):
    # support curl GET FILE and POST FILE tests:
    # Normal Operation: A large file is transfered for a period determined by timeout. When timeout expires the stats are stored.
    # Abnormal Operation Scenario 1: If the remote file is not available the test terminates after timeout expires and stas (speed, transfer bytes) take zero values.
    # Abnormal Operation Scenario 1: If the remote file transfer completes before the timeout expires (e.g. due to small file size and/or very high speed connection) then results are not recorded.
    result = {}
    timeoutExpired = False

    if mode == 'download':
        command_line = "curl -s -O " + filename + " --interface " + sourceIPaddr + " -m" + str(timeout) + " -w" + " resultSpeed=%{speed_download}\nresultSize=%{size_download}"
        logger.info(('\n\tRunning CURL HTTP DOWNLOAD FILE for Iface {}').format(iface))
    elif mode == 'upload':
        logger.info(('\n\tRunning CURL HTTP UPLOAD FILE for Iface {}').format(iface))
        command_line = "curl -u " + curlUsername + ":" + curlPassword + " -s -X POST -F filename=@" + filename + " " + curlServerResponseURL + " --interface " + sourceIPaddr + " -m" + str(timeout) + " -w" + " resultSpeed=%{speed_upload}\nresultSize=%{size_upload}"
    try:
        tbegin = time.time()
        logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tbegin))))
        output = subprocess.check_output( command_line.split(" "), shell=False )
    except subprocess.CalledProcessError as e: # this is raised when timeout expires
        timeoutExpired = True
        output = e.output
        tend = time.time()
        logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(tend))))
        #print e.returncode

        # process output
        results = output.split('\n')
        speed = results[0]
        [(m.start(0), m.end(0)) for m in re.finditer("resultSpeed=", speed)]
        speed_Mbps = float(speed[m.end(0):].split(',')[0])*8/(1000**2)
        size = results[1]
        [(m.start(0), m.end(0)) for m in re.finditer("resultSize=", size)]
        size_Mbytes = float(size[m.end(0):].split(',')[0])/(1000**2)

        # print results
        logger.info(('\t\tResults for {} seconds File Transfer over HTTP: (File: {})').format(timeout, filename))
        logger.info(("\t\t\tTransfer Speed (Mbps)   = {:.2f}").format(speed_Mbps))
        #logger.info(("\t\t\tTransfer Size  (Mbytes) = {:.2f}").format(size_Mbytes))

        # return values
        result = {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'curl', 'host': sourceIPaddr, 'filename': filename,
        'conf': {'mode': mode, 'timeout':timeout, 'ServerResponseURL': curlServerResponseURL}, 'tbegin': tbegin, 'tend': tend,
        'results': {'speed_Mbps':speed_Mbps, 'size_Mbytes':size_Mbytes}}
        return result

    # the following are executed for abnormal operation: file not found or timeout didnot expire
    logger.info("\t\t[Timeout didnot expire. Results are not considered.]")
    logger.info(("\t\tExperiment Ended at (from current system time) {}:").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))))
    result = {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'curl', 'host': sourceIPaddr, 'filename': filename,
    'conf': {'mode': mode, 'timeout':timeout, 'ServerResponseURL': curlServerResponseURL}, 'status': 'Timeout did not expire '}
    return result
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
