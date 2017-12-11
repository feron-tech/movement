#!/usr/bin/env python

# Look at specific interfaces: the list will be cross-checked with the actual interfaces detected in the system.
acceptable_ifaces            = ['eth0','op0','usb0']          # ifaces comma-separated list
# ping configuration
Nrounds                      = 1                                                        # number of rounds repeating test measurement
pingServer                   = '147.102.25.88'                                          # IP or URL to hit
pingCount                    = 5                                                        # number of ping hits
# iperf configuration
iperfServerIPaddr            = '147.102.25.88'                                          # IP or URL where iperf3 server resides #iperf.volia.net
iperfServerfPort             = 8201                                                     # port where iperf3 server listens #5201
iperfTimeToRun               = 5                                                        # time duration of iperf3 test
# speedtest configuration
speedtestServer              = 'http://147.102.25.88:8081/mini'                         #IP or URL where Speedtest Server is Hosted
# curl configuration
curlTimeout                  = 5                                                        # duration of file transfer
# curl HTTP-GET specific
curlRemoteFile               = 'http://147.102.25.88:8081/jellyfish_500MB.mkv'          # remote file location for HTTP GET
# curl HTTP-POST specific
curlLocalFile                = "/monroe/results/jellyfish_500MB_upload.mkv"             # local file location for HTTP POST
curlServerResponseURL        = "http://147.102.25.88:8081/cgi-bin/save_file.py"         # server-side file upload app
curlUsername                 = "testuser"                                               # authentication username for file upload
curlPassword                 = "testuser"                                               # authentication passworkd for file upload
# video-specific
# video probing specific
vp_args                      = ["--sub-source=marq",                                    # vlc player parameters
                                "--vout=none",
                                "--file-caching=0",
                                "--disc-caching=0",
                                "--sout-mux-caching=1500"]
vp_youtube_url               = 'https://youtu.be/WtPkFBbJLMg'                           # video url
vp_timeout                   = 3600                                                     # video test duration
# metadata related
metadataActivateFlag         = True
zmqport                      = "tcp://172.17.0.1:5556"                                  # where to listen
metadata_topic               = ""                                                       # empty string stands for all messages
topic_filters                = ["MONROE.META.DEVICE.MODEM","MONROE.META.DEVICE.GPS"]    # filter out unwanted
# filenames to store results
dataResultsFilename          = 'dataResultsFile.json'                                   # file to store data results
metadataResultsFilename      = 'metadataResultsFile.json'                               # file to store metadata results
temp_dataResultsFilename     = 'temp_dataResultsFile.json'                              # file to store (temp) data results
temp_metadataResultsFilename = 'temp_metadataResultsFile.json'                          # file to store (temp) metadata results
# logging
temp_logfilename             = 'temp_experimentLogFile.txt'
logfilename                  = 'experimentLogFile.txt'
