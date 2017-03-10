## Welcome to the _movement_ project code repository.

This repository hosts the outcomes of project MOVEMENT, a project developing open source extensions and experiments for the [EU H2020 MONROE Platform](https://www.monroe-project.eu/), as part of Open Call 1. MOVEMENT is carried out by [Feron Technologies P.C.](http://www.feron-tech.com) and [COSMOTE/OTE Group](http://www.comsote.gr).
The repository contains a set of sub-projects/experiments for measuring the quality of live or experimental mobile data networks (3G/4G/4G+). These experiments may be executed either at remote MONROE nodes or locally at any linux-based host equipped with mobile broadband devices (e.g. Wi-Fi/4G USB dongle, Mi-Fi, etc.).

### List of supported and upcoming extensions
* Systematic Mobile Data Network Benchmarking based on:
 * ping
 * iperf3 (direct, reverse)
 * speedtest (latency, download and upload speed)
 * HTTP file transfer (GET/POST)
* Video Streaming Quality (upcoming)
* VoIP Quality (upcoming)
* 4G Offloading through Wi-Fi (upcoming)

### Systematic Mobile Data Benchmarking using MONROE Nodes

#### Introduction & Code Structure
The specific software extension enables the automated execution of a set of widely used mobile data network performance tools, in MONROE nodes. The applications allow to characterize latency and throughput. Currently the following standard applications are supported:
* **ping**, for measuring RTT latency.
* **iperf3** forward and reverse TCP tests, for measuring  throughput.
* **speedtest**, for measuring latency, download and upload speed.
* **HTTP transfer** file download (GET) and upload (POST) using the ```curl``` package, for measuring throughput in both directions.

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

_:exclamation: Currently results are stored into files only. In an upcoming version, storage in a remote database will be supported._

The core functionality is organized into three files:
* [benchmarking/files/run_tests.py](benchmarking/files/run_tests.py), which includes the configuration, the metadata thread spawn, and the execution of the selected testing applications. This is the main script called in the container initialization.
* [benchmarking/files/tests.py](benchmarking/files/tests.py), which includes one function per application; each function is responsible for forming and executing the external command, capture the outcome of the command and dump results to a list.
* [benchmarking/files/metadata.py](benchmarking/files/metadata.py), which includes a single class responsible for implementing the subscription to the ZMQ MONROE application, capturing the metadata messages, apply the neccessary filters and dump messages in a json list.

The repository contains also:
* the neccessary dockerization files (docker template, main program execution script, build and push scripts)
* the command-line ```speedtest-cli``` tool for performing the speedtests (forked from https://github.com/sivel/speedtest-cli)
* a server-side python script enabling HTTP POST.

:exclamation: Support for running the application directly in local hosts is provided for ease of validation. In this case, the files containing the results are stored into the ```$HOME``` directory. The application runs as-is for the primary network interface (e.g. eth0, wlan0, wwan0, etc.), by simply calling ```python2 run_tests.py```. However, for multi-interface tests, routing rules need to be applied accordingly (modify the routing tables or create namespaces). For MONROE experiments, the result files are stored in the default ```monroe/results``` location in order to be accessible after the end of the experiment.

#### Configuration
The configuration includes 3 groups of parameters:
* A group including a set of parameters that have to be configured per testing application.
* A group of non application-specific parameters.
* A group related to metadata retrieval settings.

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
  * ```curlServerResponseURL``` : the server-side app managing the file uploading. There are plenty of approaches for developing such server-side functionality. In our implementation we use a cgi/python-based script, loaded into an Apache2 HTTP server, for which CGI scripting have to be enabled first. The script is also provided in the repository ([benchmarking/files/http-server/save_file.py](benchmarking/files/http-server/save_file.py).
  * ```curlUsername```          : HTTP POST authentication username. This is optionally added for security reasons. The server needs to be configured properly for managing authentication.
  * ```curlPassword```          : HTTP POST authentication password. This is optionally added for security reasons. The server needs to be configured properly for managing authentication.
Detailed instructions on how to configure the server side can be found at the end of the documentation. A 20 MB file which can be used for uploading is also provided in the repository ([benchmarking/files/jellyfish-5-mbps-hd-h264](benchmarking/files/jellyfish-5-mbps-hd-h264).

##### General Parameters
* ```acceptable_ifaces``` : the list of measured network interfaces (e.g. ```eth0```, ```op0```, etc.). This will be cross-checked with the list of the existing host interfaces at the begin of the experiment, in order to exclude non-present interfaces.
* ```dataResultsFilename``` : the json-formatted file where data test results are stored.
* ```metadataResultsFilename``` : the json-formatted file where metadata messages are stored.
* ```logfilename``` : the text file used to log the executed activities. For local applications this is not neccessary since we direct information/debugging messages to the system console. However for MONROE experiments this is not possible, so it could be useful to detect abnormal events.

##### METADATA Parameters
* ```zmqport```: full server/port URL where we listen for metadata messages (default: ```tcp://172.17.0.1:5556```).
* ``` metadata_topic```: the metadata type of messages to listen to (default is empty, in order to listen for all possible messages)
* ```topic_filters```: the list of type of messages to capture (e.g. ```MONROE.META.DEVICE.MODEM```, ```MONROE.META.DEVICE.GPS```)

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
In folder [benchmarking/files/sample-output](benchmarking/files/sample-output) we provide sample experimental output files.


### Instructions for setting up a server-side application supporting HTTP file transfer upload
_(The instructions have been tested in Ubuntu 14.04.5)_
* Install Apache2 and Apache2 Utils if not present: ```sudo apt-get install apache2 apache2-utils```
* Enable CGI in Apache: Follow the instructions in https://code-maven.com/set-up-cgi-with-apache ,in particular:
 * check if cgi module (```cgi.load```) is available: ```cd /etc/apache2/mods-available```
 * check if it is enabled: ```ls /etc/apache2/mods-enabled``` and if not enable it: ```sudo ln -s ../mods-available/cgi.load```
 * Reload apache:  ```sudo service apache2 reload```
 * Copy [benchmarking/files/http-server/save_file.py](benchmarking/files/http-server/save_file.py) to ```/usr/lib/cgi-bin/```
 * Create user (e.g. 'testuser'), generate and store pwd in file using apache2 util htpasswd: ```sudo htpasswd -c /usr/local/apache2_passwords testuser```
 * Modify configuration file ```/etc/apache2/conf-enabled/serve-cgi-bin.conf```  as follows:
 ```
 <IfDefine ENABLE_USR_LIB_CGI_BIN>
                ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
                <Directory "/usr/lib/cgi-bin">
                        AllowOverride None
                        Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
                        #Require all granted

                        AuthType Basic
                        AuthName "Restricted Files"
                        # (Following line optional)
                        AuthBasicProvider file
                        AuthUserFile "/usr/local/apache2_passwords"
                        Require user testuser
                </Directory>
        AddHandler cgi-script .py
        </IfDefine>
 ```
 * Reload Apache2
 Then, if ```<ServerIP/URL>``` is the Server location, set ```curlServerResponseURL``` as ``` http://<ServerIP/URL>/cgi-bin/save_file.py```


<img src="movement.png" width="50%" height="50%"/>
