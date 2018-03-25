## Voice-over-IP (VoIP) quality measurements in MONROE

The particular software extension aims at enabling MONROE platform experimenters to perform Voice-over-IP (VoIP) quality measurements.
Towards this purpose a fully automated and end-to-end custom VoIP application based on widely-used and open-source software components is developed.
The extension includes both client-side components running in any MONROE node and server-side components running in a remote Linux machine.

### Server Side
The server side of the software extension is built upon the Asterisk framework. Asterisk is a free and open source framework for building communications applications. It can run on standard Linux machines and manages VoIP communication among distributed nodes. We rely on version 13, where dial plans management is done using a mysql database. To perform an unattended installation and ready-to-run deployment we have preconfigured the most important parameters and put them into corresponding configuration files. However, these (for example the access credentials) could be easily changed by tuning the relevant files and re-installing the server. In addition:
* A VoIP registration service runs in Server for accepting incoming SIP registration requests and updating accordingly the Asterisk dial-plans. This is actually a RESTful service, and the registration procedure is performed using standard PUT, POST and DELETE messages.
* An Apache HTTP service is also deployed for providing remote access to the generated audio files to the server side.
All three components (Asterisk Server, VoIP registration Server, Apache HTTP Server) are bundled into a single container, and the required services are automatically launched at container startup.

### Client Side
The client side of the software extension is built upon the Linphone software. Linphone is an open source VoIP phone (or soft-phone) that makes possible to communicate freely with people over the Internet, using voice, video, and text instant messaging. A bash script is developed for automating the testing procedure, which is based on capturing the standard output exposed by the linphone application. A configuration file determines the IP of the remote machine hosting the VoIP server functionalities as well as the number of executed test calls per experiment.

The automated script performs the following actions:
* Retrieval of configuration parameters.
* Selection of active interfaces.
* For each detected interface we direct traffic to pass through it (using ip route commands), launch a packet-sniffer application to monitor incoming VoIP traffic, start the metadata retrieval process, and initiate the main VoIP testing procedure.
* The node id is retrieved from the MONROE node and an additional 8-char experiment id is randomly generated. A SIP registration request based on this identification is sent to the Server using a POST command. A new SIP "user" is created at the Server, for whom the access credentials correspond to the node id. In addition a new call extension based on the node id and the experiment id is stored at the Asterisk Server.
* Before the call initiation a ping test towards the Server is employed to estimate end-to-end latency.
* The linphone client initiates a call to the server and starts recording the incoming audio. The call includes the playback of a pre-recorded voice message laying the Asterisk Server.
* Upon playback completion the call is terminated and the server-side audio message is transfered to the client side using standard HTTP downloading.
* Upon call termination the client-side audio stream is also stored and packet-level statistics (packet loss, jitter, latency) are calculated at the client.
* Finally, at the client side the two audio files are fed to an open implementation of PESQ methodology, and the call quality is calculated. In addition an alternative quality metric, called e-MOS, is calculated based only on packet-level statistics. Results are stored in JSON formatted files.

### Quick Start Guide for Building and Running the Server and Client Containers

#### Server
##### Build the image

Navigate to ```voip-server``` directory and run

```docker build -t ferontech/voip-server . ```

##### Launch the container

```docker run --rm  --name voip-server -it --privileged --net=host ferontech/voip-server bash```

#### Client
##### Build the image
(Before building the image don't forget to pass the right configuration parameters into the ```experiment.cfg``` file.)

Navigate to ```voip-node``` directory and run

```docker build -t ferontech/voip-node . ```.


##### Launch the container

Either use the MONROE Scheduler or if you have direct access to the shell run the command:

```docker run --rm -it  --name voip-node-cn -v ~/path/to/store/results:/monroe/results --privileged ferontech/voip-node```
