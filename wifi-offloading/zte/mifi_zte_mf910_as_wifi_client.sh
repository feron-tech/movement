#!/bin/bash

##########################################
#chmod +x mifi_zte_mf910_as_wifi_client.sh
#sudo ./mifi_zte_mf910_as_wifi_client.sh 192.168.xx.1 temp.json zte_mifi_client
# if "sudo adb devices" results in "no permission" do "sudo adb kill-server &&  sudo adb start-server"
# zte mifi should have sim card
# need Android Debug Bridge version <= 1.0.32 (greater not working properly)
##########################################

#Make ZTE MF910 mifi a wifi client
#
#The mifi is an Android-device. 
#
# Procedure:
# 1. Log in
# 2. Switch to android mode
# 3. Enable wifi
# 4. Get IP though wpa_supplicant
# 5. Forward traffic


LOGIN_URL="/goform/goform_set_cmd_process?isTest=false&goformId=LOGIN&password=YWRtaW4%3D";
MODE_SWITCH_URL="/goform/goform_set_cmd_process?goformId=USB_MODE_SWITCH&usb_mode=6";

login_mifi()
{
    echo "Attempting MF910 login ...";

    while true;
    do
        local http_code=`curl -sL -w "%{http_code}" -o "$2" \
            -H "Referer: http://$1/index.html" \
            -H "Host: $1" \
            --connect-timeout 5 \
            "$1/$LOGIN_URL"`;

        if [ $? -ne 0 -a $http_code -ne 200 ];
        then
            echo "MF910 login failed (curl), will retry ...";
            sleep 5;
        fi

        local result=`jq '.result' $2`
        rm $2

        if [ "$result" == '"0"' ];
        then
            echo "MF910 login successful ...";
            return;
        else
            echo "MF910 login failed, will retry ...";
            sleep 5;
        fi
    done
}

switch_mifi()
{
    echo "Attempting MF910 switch to Android ...";

    while true;
    do
        local http_code=`curl -sL -w "%{http_code}" -o "$2" \
            -H "Referer: http://$1/index.html" \
            -H "Host: $1" \
            --connect-timeout 5 \
            "$1/$MODE_SWITCH_URL"`;

        if [ $? -ne 0 -a $http_code -ne 200 ];
        then
            echo "MF910 switch failed (curl), will retry ...";
            sleep 5;
        fi

        local result=`jq '.result' $2`
        rm $2

        if [ "$result" == '"success"' ];
        then
            echo "MF910 switch successful ...";
            return;
        else
            echo "MF910 switch failed, will retry ...";
            sleep 5;
        fi
    done

}

wait_for_device()
{
    while true;
    do
        adb devices | grep ZTE > /dev/null;

        if [ $? -ne 0 ];
        then
            echo "ZTE Android device not seen, sleeping five sec ...";
            sleep 5;
            continue;
        else
            echo "ZTE Android device found ...";
            break;
        fi
    done
    eval devid="$3";
    echo $devid;
    adb -s P680A1ZTED000000 shell "echo -n ${devid} > /sys/class/android_usb/android0/iSerial";
    adb kill-server; 
    adb start-server;    
}


enable_wifi()
{
    echo "Enabling wifi ...";
    eval devid="$3";
    # comment "do_configure_ar6003 $@"
    adb -s $devid shell "sed -i '296 s/^#//' /etc/init.d/wlan && sed -i '296 s/^#//' /etc/init.d/wlan_hsic";
    adb -s $devid  shell "sed -i '296 s/^/#/' /etc/init.d/wlan && sed -i '296 s/^/#/' /etc/init.d/wlan_hsic";  
    # comment "do_configure_ar6004 $@"
    adb -s $devid  shell "sed -i '303 s/^#//' /etc/init.d/wlan && sed -i '303 s/^#//' /etc/init.d/wlan_hsic";
    adb -s $devid  shell "sed -i '303 s/^/#/' /etc/init.d/wlan && sed -i '303 s/^/#/' /etc/init.d/wlan_hsic";
    adb -s $devid  shell "/etc/init.d/wlan restart";
    adb -s $devid  shell "/etc/init.d/wlan_hsic restart";
    sleep 5;

}

get_ip()
{
    eval devid="$3";	
    adb -s $devid shell "wpa_supplicant -i wlan0 -c /etc/wpa_supplicant.conf & dhcpcd wlan0" > /dev/null 2>&1 &
    while true;
    do
        ip=$(sudo adb -s "${devid}" shell "ifconfig wlan0 2> /dev/null | grep 'inet addr:' | cut -d: -f2");
	if [[ $ip ]]; then
	    echo "Got IP:" $ip;
	    break;
	else
	    echo "no IP yet ...";
            sleep 2;
	    continue;
	fi
    done
}


usb_tethering()
{
    sleep 5;
    eval devid="$3";    
    adb -s $devid shell "iptables --table nat --flush"
    adb -s $devid shell "iptables --flush"    
    adb -s $devid shell "echo 1 > /proc/sys/net/ipv4/ip_forward"
    adb -s $devid shell "iptables -A FORWARD -i bridge0 -o wlan0 -j ACCEPT"
    adb -s $devid shell "iptables -A FORWARD -i wlan0 -o bridge0 -m state --state ESTABLISHED,RELATED -j ACCEPT"
    adb -s $devid shell "iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE"
    sleep 5;
}


#Address of device is first paramter (typically 192.168.0.1 or 192.168.8.1)
#Second paramter is where to store data returned by modem (will cleaned up)
if [ $# -ne 3 ];
then
    echo "./mifi_zte_mf910_as_wifi_client.sh <IP of device> <temporary JSON storage path> <device id name>";
    exit 0;
fi

login_mifi $1 $2
switch_mifi $1 $2
wait_for_device $1 $2 $3
enable_wifi $1 $2 $3
get_ip $1 $2 $3
usb_tethering $1 $2 $3

##########################################
