#!/bin/bash

# added by antonis
mkdir /var/run/mysqld && chown -R mysql:mysql /var/lib/mysql /var/run/mysqld

term_proc() {
    /etc/init.d/asterisk stop
    /etc/init.d/mysql stop
}

trap 'term_proc' SIGTERM

/etc/init.d/mysql start

mysql -uroot -pmonroe -e "CREATE DATABASE asteriskrealtime" && mysql -uroot -pmonroe asteriskrealtime < /tmp/asteriskrealtime.sql

/etc/init.d/asterisk start

cd /root
nohup python3 -m voip_registration_server 2>/tmp/voip_registration_server.err >/tmp/voip_registration_server.log &

/bin/bash

term_proc
