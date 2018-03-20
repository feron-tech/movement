## VoLTE Experiments on MONROE Nodes

### Prerequisites
* 2 x (Android Phone connected to MONROE Node) managed via adb commands 
* Android app _CallHandler.apk_ installed on android phones (suggested version <= Android 7.1.1 Nougat) 
* Post-processing server

### Scripts
1. Run _phone1_caller.sh_ on caller MONROE Node1
  * Phone1 (connected to Node1) calls Phone2 (connected to Node2) and call is autoanswered
  * Node1 plays audio file through speaker
  * _CallHandler.apk_ records conversation in "amr-wb" format on Phone1 (caller.amr)
  * Upload recorded file and signal strength measurement file to server
2. Run _phone2_receiver.sh_ on receiver MONROE node
  * _CallHandler.apk_ records conversation in "amr-wb" format on Phone2 (receiver.amr) and autoanswer call
  * Upload recorded file and signal strength measurement file to server
3. Run _server_postprocessing.sh_ on server
  * Post-process caller and receiver recorded files (convert to wav, synchornize and compare quality using PESQ) 
  * Results are stored in _output.txt_


