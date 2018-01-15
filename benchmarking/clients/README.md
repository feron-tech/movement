### Systematic Mobile Network Benchmarking using MONROE Nodes

#### Introduction & Code Structure
The specific software extension enables the automated execution of a set of widely used mobile data network performance tools, in MONROE nodes. The applications allow to characterize latency and throughput. Currently the following standard applications are supported:
* **ping**, for measuring RTT latency.
* **iperf3** forward and reverse TCP tests, for measuring  throughput.
* **speedtest**, for measuring latency, download and upload speed.
* **HTTP transfer** file download (GET) and upload (POST) using the ```curl``` package, for measuring throughput in both directions.
* **Video Streaming**, i.e. playing a video from a remote server (youtube or standalone server), for measuring various quality of service and experience indicators. The VLC client has been selected to be the core of our video testing tool, thanks to the availability of an extensive open API/library which exposes various video streaming parameters and performance indicators. Currently, the tool is able to automatically stream both YouTube videos (using a parser) and videos stored to dedicated servers. Various video quality levels (including 1080p) and network caching configurations are being supported. The tool enables the capture of a set of application-level quality of service/experience indicators, such as:
  * video playback initiation latency,
  * number of (potential) video stalls,
  * progress of video playing time vs. the actual time,
  * application bit-rate.

The extension is developed in Python (python 2 is currently fully tested and validated) and uses the _subprocess_ module to call the external command-line applications. Back-end public or private server applications are required for executing the experiments (e.g. iperf3 server, HTTP server, etc.).

The experiment is organized in the following steps:
* Selection & configuration of testing application parameters (e.g. servers to hit, duration of experiment, etc.).
* Start capturing metadata (e.g. MODEM and GPS messages) in the background, using a dedicated thread.
* Run the selected testing applications serially. For each application:
  * Form and execute an external system command using the _subprocess_ python module;
  * Capture the generated output (in string or json format) and filter out the corresponding KPI(s) information (e.g. latency, throughput, bytes transferred, etc.);
  * Insert the results in a json-formatted list;
  * (Optional) Log step-by-step experiment output for debugging purposes into a separate file.
* Dump measurement results and retrieved metadata in json-formatted files.
* (Optional) Store measurement results in a Mongo database

The core functionality is organized into 4 files:
* [clients/files/config.py](clients/files/config.py), which includes the experiment configuration.
* [clients/files/run_tests.py](clients/files/run_tests.py), which includes the execution of the selected testing applications and is also responsible for spawning the metadata thread. The results are formated as json entries and are dumped to a file and optionally to a database. This is the main script called in the container initialization.
* [clients/files/tests.py](clients/files/tests.py), which includes one function per application; each function is responsible for forming and executing the external command, capture the outcome of the command and dump results to a list.
* [clients/files/metadata.py](clients/files/metadata.py), which includes a single class responsible for implementing the subscription to the ZMQ MONROE application, capturing the metadata messages, apply the neccessary filters and dump messages in a json list.

The repository contains also:
* the neccessary dockerization files (docker template, main program execution script, build and push scripts)
* the command-line ```speedtest-cli``` tool for performing the speedtests (forked from https://github.com/sivel/speedtest-cli)

:exclamation: Support for running the application directly in local hosts is provided for ease of validation. In this case, the files containing the results are stored into the ```$HOME``` directory. The application runs as-is for the primary network interface (e.g. eth0, wlan0, wwan0, etc.), by simply calling ```python2 run_tests.py```. However, for multi-interface tests, routing rules need to be applied accordingly (modify the routing tables or create namespaces). For MONROE experiments, the result files are stored in the default ```monroe/results``` location in order to be accessible after the end of the experiment.

#### Configuration

#### Global Configuration
The configuration includes 5 groups of parameters:
* A group including a set of parameters that have to be configured per testing application.
* A group of non application-specific parameters.
* A group related to metadata retrieval settings.
* A group related to storage of results and logging information into text filenames
* A group related to storage of results to a Mongo database

#### Network Configuration
Special attention needs to be paid for multi-interface experiments. We provide two means to enforce traffic to be routed to a specific interface:
* Per-application interface binding: Many command-line tools, such as ```ping```, ```iperf3```, ```curl```, and ```speedtest``` expose explicit interface binding. In this case we use the relevant argument to route traffic.
* Global traffic routing: In case the application does not expose an explicit interface binding, we configure a set of IP routes appropriately. This is done as follows:
  * Get the lookup table index for the current interface
  * Add a temporary IP rule to route all traffic to specific interface
  * At the end of the experiment we delete the temporary rule

##### Application-Specific Parameters

###### PING
* ```pingServer```: the Server IP or URL to hit (examples: ```google.com```, ```8.8.8.8```, etc.)
* ```pingCount``` : the number of ping requests (e.g. ```5```, ```10```, etc.)

###### iperf3
* ```iperfServerIPaddr``` : the Server IP or URL where iperf3 server resides (public or private)
* ```iperfServerfPort```  : the port where the Server listens to (default: ```5201```)
* ```iperfTimeToRun```    : the duration of the test (e.g. ```5```, ```10```, etc.)

In order to execute iperf3 tests, an iperf3 server needs to be deployed. A list of publicly available servers (e.g. ```iperf.volia.net```) as well as instructions for deploying a private server may be found [here](https://iperf.fr/iperf-servers.php) and [here](https://iperf.fr/iperf-download.php#ubuntu).

###### SPEEDTEST
* ```speedtestServer``` : the public/private speedtest server IP/URL. A list of publicly available speedtest servers may be found in [this link](https://www.speedtest.net/speedtest-servers.php) (e.g. speedtest.otenet.gr), whereas instructions for how to setup a private Speedtest server may be found [here](http://www.tecmint.com/speedtest-mini-server-to-test-bandwidth-speed/).

###### HTTP File Transfer
* ```curlTimeout``` : The duration of HTTP transfer in seconds (e.g. ```5```, ```10```). The file size is considered large enough such that the transfer is not completed before timeout expires. When the timeout expires the average transfer speed is calculated. If the transfer is completed before the expiration of the timeout interval, the results are dropped. By keeping the transfer time fixed (and not keeping the file size fixed) we provide a fair comparison between technologies with large speed differentiation, for example 3G vs 4G (refer to ETSI TR 102 678 V1.1.1 (2009-11) for a discussion on this issue).
* For HTTP GET (File Download):
  * ```curlRemoteFile``` : the complete URL of the file to be downloaded. One could use either a publicly available URL or deploy a private HTTP Server (e.g. Apache2) and host a target file.
* For HTTP POST (File Upload):
  * ```curlLocalFile``` : the full path of the local file to be uploaded.
  * ```curlServerResponseURL``` : the server-side app managing the file uploading. There are plenty of approaches for developing such server-side functionality. In our implementation we use a cgi/python-based script, loaded into an Apache2 HTTP server, for which CGI scripting have to be enabled first. The script is also provided in the repository ([benchmarking/files/http-server/save_file.py](benchmarking/files/http-server/save_file.py)).
  * ```curlUsername```          : HTTP POST authentication username. This is optionally added for security reasons. The server needs to be configured properly for managing authentication.
  * ```curlPassword```          : HTTP POST authentication password. This is optionally added for security reasons. The server needs to be configured properly for managing authentication.
Detailed instructions on how to configure the server side can be found at the end of the documentation. A 20 MB file which can be used for uploading is also provided in the repository ([benchmarking/files/jellyfish-5-mbps-hd-h264.mkv](benchmarking/files/jellyfish-5-mbps-hd-h264.mkv)).

###### Video Streaming Test
* ```vp_youtube_url``` : the URL of the video file to play. This could be link to a public Youtube video or to a private video server. For Youtube videos, it seems that the ```1280x720``` resolution is selected by default. For enforcing another resolution, including ```1920x1080```, explicit links from https://www.h3xed.com/blogmedia/youtube-info.php could be used.
* ```vp_timeout ```    : the maximum duration of the video test. If this is exceeded the test is aborted. This is useful in case that bad channel/network conditions occur and the video stalls indefinitely.
* ```vp_args  ```      : VLC player configuration, including caching, output, etc.

##### General Parameters
* ```acceptable_ifaces``` : the list of measured network interfaces (e.g. ```eth0```, ```op0```, etc.). This will be cross-checked with the list of the existing host interfaces at the begin of the experiment, in order to exclude non-present interfaces.
* ```dataResultsFilename``` : the json-formatted file where data test results are stored.
* ```metadataResultsFilename``` : the json-formatted file where metadata messages are stored.
* ```logfilename``` : the text file used to log the executed activities. For local applications this is not neccessary since we direct information/debugging messages to the system console. However for MONROE experiments this is not possible, so it could be useful to detect abnormal events.

##### METADATA Parameters
* ```zmqport```: full server/port URL where we listen for metadata messages (default: ```tcp://172.17.0.1:5556```).
* ``` metadata_topic```: the metadata type of messages to listen to (default is empty, in order to listen for all possible messages)
* ```topic_filters```: the list of type of messages to capture (e.g. ```MONROE.META.DEVICE.MODEM```, ```MONROE.META.DEVICE.GPS```)
* ```metadataActivateFlag```: a boolean flag activating/deactivating metadata retrieval

##### DATABASE storage
* ```storeToDb```: flag for activating/deactivating storage of data results into a mongo db.
* ```dbname```: name of the database to store results
* ```dbuser``` and ```dbpassword```: credentials to access to the DATABASE
* ```dbhost``` and ```dbport```: where the Mongo instance resides
* ```dbCollectionName``` : the collection name

#### Typical Experimental Output
Each measurement test corresponds to one entry into a json-formatted list, and contains information about the configuration of the experiment (host, server, interface, nodeid, selected parameters), the starting and ending times, and the estimated KPIs. Sample measurement records are provided below:

#### PING
```
{
	"_id": "c45327ca-04e5-11e7-91f1-0242ac110002",
	"app": "ping",
	"conf": [
		5
	],
	"host": "192.168.236.187",
	"iface": "op0",
	"nodeid": "171",
	"results": {
		"avg": 41.287,
		"max": 59.329,
		"min": 23.992
	},
	"server": "google.com",
	"tbegin": 1489077050.418206,
	"tend": 1489077054.582648
}
```
#### iperf3 (reverse)
```
{
	"_id": "cc47f708-04e5-11e7-91f1-0242ac110002",
	"app": "iperf3",
	"conf": {
		"mode": "receive",
		"timeToRun": 5
	},
	"host": "192.168.236.187",
	"iface": "op0",
	"nodeid": "171",
	"results": {
		"received_bitrate_Mbps": 18.8433056819909,
		"sender_bitrate_Mbps": 19.155785583437993
	},
	"server": "iperf.volia.net",
	"tbegin": 1489077061.321093,
	"tend": 1489077067.934453
}
```
#### SPEEDTEST
```
{
	"_id": "ddb155de-04e5-11e7-91f1-0242ac110002",
	"app": "speedtest",
	"host": "192.168.236.187",
	"iface": "op0",
	"nodeid": "171",
	"results": {
		"downloadBitrateMbps": 17.360335312420972,
		"pingmsec": 67.664,
		"uploadBitrateMbps": 14.095585038873505
	},
	"server": "http://52.174.152.255/mini/",
	"tbegin": 1489077067.938697,
	"tend": 1489077097.145396
}
```

#### HTTP File Transfer (download)
```
{
	"_id": "e0b52a30-04e5-11e7-91f1-0242ac110002",
	"app": "curl",
	"conf": {
		"ServerResponseURL": "",
		"mode": "download",
		"timeout": 5
	},
	"filename": "http://52.174.152.255/jellyfish-120-mbps-4k-uhd-h264.mkv",
	"host": "192.168.236.187",
	"iface": "op0",
	"nodeid": "171",
	"results": {
		"size_Mbytes": 11.625654,
		"speed_Mbps": 18.611344
	},
	"tbegin": 1489077097.15086,
	"tend": 1489077102.204858
}
```

#### Video Streaming (VLC-based)
```
{
	"_id": "2f68dbfa-623c-11e7-b921-0242ac110002",
	"app": "vlc",
	"conf": {
		"VideoStreamingURL": "https://youtu.be/WtPkFBbJLMg",
		"network_caching": "--file-caching=0",
		"timeout": 3600
	},
	"host": "192.168.0.173",
	"iface": "op0",
	"nodeid": "175",
	"results": {
		"Nstalls": 0,
		"init_delay": 1.7260780334472656,
		"input_bitrates": [
			0.0,
			0.0,
			0.0,
			0.0,
			2241.8315410614014,
			1223.2468128204346,
			820.0439810752869,
			1544.584035873413,
			917.9500341415405,
			1166.8622493743896,
			1166.8622493743896,
			1025.6614685058594,
			1301.876187324524,
			1040.130376815796,
			1001.866340637207,
			1003.5899877548218,
			1003.5899877548218,
			1369.5205450057983,
			958.9923024177551,
			971.7546105384827,
			1365.7389879226685,
			1331.9141864776611,
			876.8774271011353,
			876.8774271011353,
			999.0349411964417,
			1053.0998706817627,
			1053.0998706817627,
			1638.7465000152588,
			1149.4606733322144,
			223.04105758666992,
			223.04105758666992,
			194.7897970676422
		],
		"video_sizes": [
			"(1280L, 720L)",
			"(0L, 0L)"
		]
	},
	"timestamp_begin": 1499339596.994916,
	"timestamp_end": 1499339629.102839
}
```

In folder [clients/files/sample-output](clients/files/sample-output) we provide sample experimental output files.
