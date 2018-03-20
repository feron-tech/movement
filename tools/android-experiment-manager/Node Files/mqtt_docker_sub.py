#!/usr/bin/python

import time
import paho.mqtt.client as mqtt
import subprocess

time.sleep(10)

###################################
# Initialization
broker = "192.168.1.2"
username = "user"
password = "pass"

# docker image
dockerimage = "ferontech/bench-node-mqtt"

# node id will be retrieved from '/etc/nodeid'
nodeid = "175"
with open('/etc/nodeid') as nodeidfd:
    nodeid = nodeidfd.readline().rstrip()

###################################
# Docker commands
startCommand = "docker run -i -e mqtt_param='yes' -v /etc:/etc -v /home/monroeSA/msr/new:/monroe/results --net=host  --privileged --name mydocker " + dockerimage
stopCommand = "docker stop mydocker"
rmCommand = "docker rm mydocker"
psCommand = "docker ps"

###################################
# MQTT functions definition

# The callback for when the client receives a CONNACK response from the server.
def on_connect(self, client, userdata, rc):
    print("Connected with result code "+str(rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    #print("Received: " + msg.topic+" "+str(msg.payload))
    if msg.topic == ("monroe/" + nodeid  + "/docker") and msg.payload == "startdocker":
        print("---------Command Received: " + msg.topic+" "+str(msg.payload))
        subprocess.call(['bash','-c', stopCommand])
        subprocess.call(['bash','-c', rmCommand])
        subprocess.Popen(startCommand, shell=True)
    if msg.topic == ("monroe/" + nodeid  + "/docker") and msg.payload == "psdocker":
        print("---------Command Received: " + msg.topic+" "+str(msg.payload))
        output = subprocess.check_output(['bash','-c', psCommand])
        print output
        output = "mydocker is running" if ('mydocker' in output) else "mydocker is not running"
        client.publish("monroe/" + nodeid  + "/dockerFB", output)
    if msg.topic == ("monroe/" + nodeid  + "/docker") and msg.payload == "stopdocker":
        print("---------Command Received: " + msg.topic+" "+str(msg.payload))
        output = subprocess.check_output(['bash','-c', stopCommand])
        print output
        output = subprocess.check_output(['bash','-c', rmCommand])
        print output

def on_publish(client, userdata, mid):
	pass

def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


###################################
# Connect to MQTT broker

client = mqtt.Client()
client.username_pw_set(username,password)
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.on_subscribe = on_subscribe

client.connect(broker, 1883)

client.subscribe("monroe/" + nodeid  + "/docker")

client.loop_forever() 

