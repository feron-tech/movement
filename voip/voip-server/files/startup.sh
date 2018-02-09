#!/bin/bash

# this is added to resolve a bug on loading for the first time mysql
mkdir /var/run/mysqld && chown -R mysql:mysql /var/lib/mysql /var/run/mysqld

term_proc() {
	/etc/init.d/asterisk stop
	/etc/init.d/mysql stop
	/etc/init.d/apache2 stop
}

trap 'term_proc' SIGTERM

/etc/init.d/mysql start

mysql -uroot -pmonroe -e "CREATE DATABASE asteriskrealtime" && mysql -uroot -pmonroe asteriskrealtime < /tmp/asteriskrealtime.sql

/etc/init.d/asterisk start

echo "ServerName localhost" >> /etc/apache2/apache2.conf && /etc/init.d/apache2 start

cd /root
nohup python3 -m voip_registration_server 2>/tmp/voip_registration_server.err >/tmp/voip_registration_server.log &

ln -s  /var/spool/asterisk/monitor /var/www/html/asterisk-files
cd  /var/spool/asterisk/monitor

cd /root && /bin/bash

term_proc
