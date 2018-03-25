## MQTT subscription programs

### Prerequisites
* MQTT-based docker image pulled on MONROE node (e.g. _ferontech/bench-node-mqtt_)
* Python package _paho-mqtt_

### Initialization 
* Edit _/etc/rc.local_
* Make it executable (``` sudo chmod +x /etc/rc.local ```)
* Create the following files
  * /home/monroeSA/Documents/mqtt_docker_sub.sh
  * /home/monroeSA/Documents/mqtt_docker_sub.py (edit to personalize broker IP and credentials)
* Change ownership and permissions
  * ``` sudo chmod u+x /home/monroeSA/Documents/mqtt_docker_sub.sh ```
  * ``` sudo chmod u+x /home/monroeSA/Documents/mqtt_docker_sub.py ```
  * ``` sudo chown monroeSA:monroeSA /home/monroeSA/Documents/mqtt_docker_sub.sh ```
  * ``` sudo chown monroeSA:monroeSA /home/monroeSA/Documents/mqtt_docker_sub.py ```
* Restart 'rc-local' service
  * ``` sudo systemctl restart rc-local.service ```










