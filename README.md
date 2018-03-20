## Welcome to the _movement_ project code repository.

This repository hosts the outcomes of project MOVEMENT, a project developing open source extensions and experiments for the [EU H2020 MONROE Platform](https://www.monroe-project.eu/), as part of Open Call 1. MOVEMENT is carried out by [Feron Technologies P.C.](http://www.feron-tech.com) and [COSMOTE/OTE Group](http://www.comsote.gr).
The repository contains a set of sub-projects/experiments for measuring the quality of live or experimental mobile data networks (3G/4G/4G+) including support for WiFi technologies. These experiments may be executed either at remote MONROE nodes or locally at any linux-based host equipped with mobile broadband devices (e.g. Wi-Fi/4G USB dongle, Mi-Fi, etc.).

### List of software extensions
- Mobile network **benchmarking** based on widely-used data testing applications:
	- Ping
	- iperf3 (direct, reverse)
	- Speedtest by Ookla
	- HTTP file transfer (upload/download)
	- Video streaming on demand using the open-source VLC player (Youtube or private video files)
- **VoIP** testing and quality evaluation using open-source tools:
  - Asterisk VoIP Server
  - Linphone VoIP Client
- **WiFi/Offloading** experiments:
  - Test WiFi quality
  - 4G Offloading through Wi-Fi

Except for the primary software tools shown above we also provide two additional extensions helping MONROE experimenters to:
* Control experiments using a Smartphone application and an MQTT-based messaging framework;
* Perform automated mobile-to-mobile VoLTE test call and analysis using VoLTE-enabled smartphones.

### Repository Structure
* benchmarking : software extensions for data and video testing
  * bench-node : the client applications (loaded in MONROE nodes)
  * bench-server : the server-side applications needed to perform the client tests (dockerized for easy deployment)
* voip : software extensions for voice-over-IP testing
  * voip-node   : the client application loaded in MONROE nodes
  * voip-server : the server-side applications needed to perform the client tests (dockerized for easy deployment)
* wifi-offloading : software extensions related to wifi testing
  * monroeap : Preparation of a docker image for enabling MONROE node to operate as WiFi Access Point and 4G/WiFi router
  * zte : 4G/WiFi offloading tests using the ZTE MF-910 MiFi devices of MONROE hardware v1.
* tools: other extensions not belonging to the above categories
  * android-experiment-manager: MQTT-based framework to easily control MONROE experimentation process (configure, initiate, monitor, store results) using a smartphone app.
  * volte-testing: scripts for automatically performing  mobile-to-mobile VoLTE test calls in VoLTE-enabled smartphones and analyze recorded audio samples.  

<img src="movement.png" width="50%" height="50%"/>
