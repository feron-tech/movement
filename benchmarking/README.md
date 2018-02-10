## Systematic Mobile Network Benchmarking using MONROE Nodes

The specific software extension enables the automated execution of a set of widely used mobile data network performance tools, in MONROE nodes. The extension allows to characterize various QoS and QoE indicators, depending on the testing application. Currently the following standard applications are supported:
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
* (optional) Start capturing metadata (e.g. MODEM and GPS messages) in the background, using a dedicated thread.
* (optional) Start sniffing the detected interface for acquiring packet-level statistics, such as packet loss, jitter, etc.
* Configure global traffic routing for specific tested interface or if allowed bind application to specific interface.
* Run the selected testing applications serially. For each application:
  * Form and execute an external system command using the _subprocess_ python module;
  * Capture the generated output (in string or json format) and filter out the corresponding KPI(s) information (e.g. latency, throughput, bytes transferred, etc.);
  * Insert the results in a json-formatted list;
  * (Optional) Log step-by-step experiment output for debugging purposes into a separate file.
* Dump measurement results and retrieved metadata in json-formatted files.
* (Optional) Store measurement results in a Mongo database


### Quick Start Guide for Building and Running the Server and Client Containers

#### Client
##### Build the image
(Before building the image don't forget to pass the right configuration parameters into the ```config``` file.)

Navigate to ```clients``` directory and run ```./build.sh ```

##### Launch the container

Either use the MONROE Scheduler or if you have direct access to the shell run the command:

```docker run --rm -it --name clientcn -v /path/to/store/results:/monroe/results --privileged clients```

#### Server
##### Build/Pull the images

Navigate to ```server``` directory and run ```./build.sh ```

(Optional) For storing results to a MongoDB: ```docker pull mongo:latest```

##### Launch the containers

``` docker run --rm -idt --name servercn --privileged -p 8081:80 -p 8201-8204:5201-5204 servers ```

(Optional) For storing results to a MongoDB (detailed instructions in Server README file): ```docker run --rm -d --name mongocn -p 54024:27017 -v ~/mongodb_data:/data/db mongo```
