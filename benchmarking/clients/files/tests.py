# Authors: Antonis Gotsis, Demetrios Vasiliades (Feron Technologies P.C.)
# Date: May 2016
# License: GNU AFFERO GENERAL PUBLIC LICENSE Version 3
# Developed for use by the EU H2020 MONROE OC2 MOVEMENT project
# Summary: Contains the full functionality for each test. One function per test type is defined.

import time        # needed for managing time
import subprocess  # needed for calling external shell commands
import re          # needed for string search procedures
import uuid        # needed for generating a unique id for JSON recording
import json        # needed for processing/storing formated results
import sys,os      # needed for sys and os functionalities calling
from datetime import datetime
import urllib2

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def ping_test(iface, experimentConfig, serverIPaddr, sourceIPaddr, numberOfPings, logger,  bindToIface=True):
	# supports typical ping test
	if bindToIface:
		command_line = "ping -c " + str(numberOfPings) + " -I " + sourceIPaddr + " " + serverIPaddr
	else:
		command_line = "ping -c " + str(numberOfPings) + " " + serverIPaddr
	logger.info('\n\tRunning PING for Iface {}'.format(iface))
	try:
		timestamp_begin = time.time()
		logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_begin))))
		# the output is in string format
		output = subprocess.check_output(command_line.split(" "),shell=False)
		timestamp_end = time.time()
		logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_end))))

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
		'timestamp_begin': timestamp_begin, 'timestamp_end': timestamp_end, 'results': {'avg': summaryVals[1], 'min': summaryVals[0], 'max': summaryVals[2]}}
	except subprocess.CalledProcessError as exc:
		#logger.info(("\tUnable to complete ping experiment. Error code:{}, Error message: {}").format(exc.returncode, str(exc)))
		return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'ping', 'host': sourceIPaddr, 'server': serverIPaddr, 'conf': [numberOfPings],
		'exception_error':str(exc)}
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def iperf3_test(iface, experimentConfig, serverIPaddr, serverPort, timeToRun, mode, sourceIPaddr, logger,  bindToIface=True):
	# supports iperf3 TCP SEND/RECEIVE tests
	if bindToIface:
		command_line = "iperf3 -c " + serverIPaddr + " -p " + str(serverPort) + " -B " + sourceIPaddr + " -t " + str(timeToRun) + " -J"
	else:
		command_line = "iperf3 -c " + serverIPaddr + " -p " + str(serverPort) + " -t " + str(timeToRun) + " -J"
	# if mode is receive add -R flag
	if mode == 'send':
		logger.info(('\n\tRunning iperf3 UPLOAD for Iface {}').format(iface))
	elif mode == 'receive':
		command_line = command_line + ' -R'
		logger.info(('\n\tRunning iperf3 DOWNLOAD for Iface {}').format(iface))
	try:
		timestamp_begin = time.time()
		logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_begin))))
		output = subprocess.check_output(command_line.split(" "),shell=False)
		timestamp_end = time.time()
		logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_end))))
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
		'conf': {'mode': mode, 'timeToRun':timeToRun}, 'timestamp_begin': timestamp_begin, 'timestamp_end': timestamp_end,
		'results': {'received_bitrate_Mbps':received_bitrate_Mbps, 'sender_bitrate_Mbps':sender_bitrate_Mbps}}

	except Exception as exc:
		logger.info(("\tUnable to complete iperf experiment. Error message {}").format(str(exc)))
		return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'iperf3', 'host': sourceIPaddr, 'server': serverIPaddr,
		'conf': {'mode': mode, 'timeToRun':timeToRun},'exception_error':str(exc)}
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def curl_test(iface, experimentConfig, filename, sourceIPaddr, timeout, mode, logger, curlServerResponseURL="", curlUsername="", curlPassword="", bindToIface=True):
	# support curl GET FILE and POST FILE tests:
	# Normal Operation: A large file is transfered for a period determined by timeout. When timeout expires the stats are stored.
	# Abnormal Operation Scenario 1: If the remote file is not available the test terminates after timeout expires and stas (speed, transfer bytes) take zero values.
	# Abnormal Operation Scenario 2: If the remote file transfer completes before the timeout expires (e.g. due to small file size and/or very high speed connection) then results are not recorded.
	result = {}
	timeoutExpired = False
	deadLinkFound = False # boolean variable to check if file exists
	if mode == 'download':
		logger.info(('\n\tRunning CURL HTTP DOWNLOAD FILE for Iface {}').format(iface))
		if bindToIface:
			command_line = "curl -s -O " + filename + " --interface " + sourceIPaddr + " -m" + str(timeout) + " -w" + " resultSpeed=%{speed_download}\nresultSize=%{size_download}"
		else:
			command_line = "curl -s -O " + filename + " -m" + str(timeout) + " -w" + " resultSpeed=%{speed_download}\nresultSize=%{size_download}"
		try:
			urllib2.urlopen(urllib2.Request(filename))
			deadLinkFound = False
		except:
			deadLinkFound = True
	elif mode == 'upload':
		logger.info(('\n\tRunning CURL HTTP UPLOAD FILE for Iface {}').format(iface))
		if bindToIface:
			command_line = "curl -u " + curlUsername + ":" + curlPassword + " -s -X POST -F filename=@" + filename + " " + curlServerResponseURL + " --interface " + sourceIPaddr + " -m" + str(timeout) + " -w" + " resultSpeed=%{speed_upload}\nresultSize=%{size_upload}"
		else:
			command_line = "curl -u " + curlUsername + ":" + curlPassword + " -s -X POST -F filename=@" + filename + " " + curlServerResponseURL + " -m" + str(timeout) + " -w" + " resultSpeed=%{speed_upload}\nresultSize=%{size_upload}"
		deadLinkFound = not (os.path.exists(filename))
	if not deadLinkFound:
		try:
			timestamp_begin = time.time()
			logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_begin))))
			output = subprocess.check_output( command_line.split(" "), shell=False )
		except subprocess.CalledProcessError as e: # this is raised when timeout expires
			timeoutExpired = True
			output = e.output
		#logger.info((output))

		timestamp_end = time.time()
		logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_end))))
		#print e.returncode
		# process output
		results = output.split('\n')
		if timeoutExpired is True:
			logger.info("\t\t[Timeout expired.]")
			speed = results[0]
			size = results[1]
		else:
			logger.info("\t\t[Timeout did not expire.]")
			if mode == 'download':
				speed = results[0]
				size = results[1]
			elif mode == 'upload':
				speed = results[9]
				size = results[10]
				
		# Calcs
		[(m.start(0), m.end(0)) for m in re.finditer("resultSpeed=", speed)]
		speed_Mbps = float(speed[m.end(0):].split(',')[0])*8/(1000**2)
		[(m.start(0), m.end(0)) for m in re.finditer("resultSize=", size)]
		size_Mbytes = float(size[m.end(0):].split(',')[0])/(1000**2)
		# print results
		logger.info(('\t\tResults for {} seconds File Transfer over HTTP: (File: {})').format(timeout, filename))
		logger.info(("\t\t\tTransfer Speed (Mbps)   = {:.2f}").format(speed_Mbps))
		#logger.info(("\t\t\tTransfer Size  (Mbytes) = {:.2f}").format(size_Mbytes))
		# return values
		result = {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'curl', 'host': sourceIPaddr, 'filename': filename,
		'conf': {'mode': mode, 'timeout':timeout, 'ServerResponseURL': curlServerResponseURL}, 'timestamp_begin': timestamp_begin, 'timestamp_end': timestamp_end,
		'results': {'speed_Mbps':speed_Mbps, 'size_Mbytes':size_Mbytes}}
		return result

	else:
		# the following are executed for abnormal operation: file not found or timeout didnot expire
		logger.info("\t\t[File not found. Results are not considered.]")
		logger.info(("\t\tExperiment Ended at (from current system time) {}:").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(time.time()))))
		result = {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'curl', 'host': sourceIPaddr, 'filename': filename,
		'conf': {'mode': mode, 'timeout':timeout, 'ServerResponseURL': curlServerResponseURL}, 'status': 'File not found.'}
		return result
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def speedtest_test(iface, experimentConfig, serverURL, sourceIPaddr, logger, bindToIface=True):
	# supports command-line speedtest using speedtest-cli
	if bindToIface:
		command_line = "/opt/monroe/speedtest-cli --mini " + serverURL + " --source " + sourceIPaddr + " --json"
	else:
		command_line = "/opt/monroe/speedtest-cli --mini " + serverURL + " --json"
	logger.info(('\n\tRunning SPEEDTEST for Iface {}').format(iface))
	try:
		# execute experiment
		timestamp_begin = time.time()
		logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_begin))))
		output = subprocess.check_output(command_line.split(" "),shell=False)
		timestamp_end = time.time()
		logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_end))))

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
		'timestamp_begin': timestamp_begin, 'timestamp_end': timestamp_end, 'results': {'downloadBitrateMbps': downloadBitrateMbps, 'uploadBitrateMbps': uploadBitrateMbps, 'pingmsec': pingmsec}}

	except subprocess.CalledProcessError as exc:
		logger.info(("\tUnable to perform speedtest experiment. Error code:{}.  Error message: {}").format(exc.returncode, str(exc)))
		return {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'speedtest', 'host': sourceIPaddr, 'server': serverURL,
		'exception_error':str(exc)}
#--------------------------------------------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------------------------------------------
def video_streaming_probe_test(iface, experimentConfig, sourceIPaddr, vlc_args, youtube_url, timeout_secs, VideoStreamingProbe, logger):
	logger.info('\n\tRunning Video Streaming Probe for Iface {} (URL: {})'.format(iface, youtube_url))
	timestamp_begin = time.time()
	logger.info(("\t\tExperiment Started at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_begin))))
	try:
		video_buffering_events,start_sys_time,errorFlg,stats_results = VideoStreamingProbe(vlc_args).start_probing(youtube_url, timeout_secs, logger)
		timestamp_end = time.time()
		logger.info(("\t\tExperiment Ended   at (from current system time)  : {}").format(time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(timestamp_end))))

		video_size_results = []
		input_bitrate_results = []
		for i in stats_results:
			video_size_results.append(i['video_size'])
			input_bitrate_results.append(i['input_bitrate']*8000)
			#print('%s;%s;%s;%s' % (i['current_time'], int((i['sys_time'] - start_sys_time) * 1000),  i['video_size'], i['input_bitrate']*8000))

		# post-process
		if errorFlg:
			logger.info('\t\t-- Video failed')
		else:
			logger.info('\t\t\n-- Overall stats')
			buf_events_percs = []
			buf_events_timestamps = []
			buf_events_duration = []

			for i in video_buffering_events:
				buf_events_timestamps.append(i[0])
				buf_events_percs.append(i[1])
				buf_events_duration.append(max(0, i[0] - start_sys_time))

			buf_perc_100 = []
			buf_perc_0 = []

			for i, j in enumerate(buf_events_percs): # i is the index
				if abs(j-100.0)<=0.01:
					buf_perc_100.append(i)
				if abs(j-0.0)<=0.01:
					buf_perc_0.append(i)

			# case-by-case analysis
			if not buf_perc_100: # case 1: Video did not start at all
				logger.info("No single buffering procedure completed (Video did not start at all)")
				Nstalls = -1;
				init_delay = -1;
			else:
				# init delay
				init_delay = buf_events_duration[buf_perc_100[0]]
				logger.info(("---- initial delay (s) = {:.2f}").format(init_delay))
				buf_perc_0 = [value for value in buf_perc_0 if value > buf_perc_100[0]]
				buf_perc_100.pop(0)
				# stall events
				Nstalls = 0;
				stalls_dur = []
				while True:
					if (buf_perc_0 and buf_perc_100):
						# another completed buffering event occured
						Nstalls = Nstalls + 1
						temp0 = [value for value in buf_perc_0 if value < buf_perc_100[0]]
						event_delay = buf_events_duration[buf_perc_100[0]] - buf_events_duration[temp0[-1]]
						stalls_dur.append(event_delay)
						logger.info(("--- stall event # {} (started at {:.2f} ... estimated duration (s) = {:.2f}) ").format(Nstalls,buf_events_duration[temp0[-1]],event_delay))
						buf_perc_0 = [value for value in buf_perc_0 if value > buf_perc_100[0]]
						buf_perc_100.pop(0)
						if not (buf_perc_0 and buf_perc_100):
							break
					elif (buf_perc_0 and not(buf_perc_100)):
						# another incomplete buffering event occured
						Nstalls = Nstalls + 1
						stalls_dur.append(-1)
						logger.info(("---- stall event # {} (started at {:.2f} ... incomplete) ").format(Nstalls, buf_events_duration[buf_perc_0[-1]]))
						break
					# check for termination
					if not(buf_perc_0 and buf_perc_100):
						break;
				if Nstalls == 0:
					logger.info ("---- no stalls occured")

			# return values
			result = {'_id': str(uuid.uuid1()), 'nodeid': experimentConfig['nodeid'], 'iface': iface, 'app': 'vlc', 'host': sourceIPaddr,
			'conf': {'timeout':timeout_secs, 'VideoStreamingURL': youtube_url, 'network_caching': vlc_args[2]}, 'timestamp_begin': timestamp_begin, 'timestamp_end': timestamp_end,
			'results': {'init_delay':init_delay, 'Nstalls':Nstalls, 'video_sizes':list(set(video_size_results)), 'input_bitrates':input_bitrate_results}}
			return result


	except Exception, ex:
		logger.info('\tAn error occured during Video Streaming Probe [{}-{}]'.format(str(ex.__class__.__name__), str(ex)))
#--------------------------------------------------------------------------------------------------------------------------------------------------------------
