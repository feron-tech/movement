#!/bin/bash

apt-get update
apt-get install -y debconf-utils

echo mysql-server-5.5 mysql-server/root_password password monroe | debconf-set-selections
echo mysql-server-5.5 mysql-server/root_password_again password monroe | debconf-set-selections

apt-get install -y wget build-essential pkg-config sqlite3 libsqlite3-dev libjansson-dev autoconf automake libtool libxml2-dev libncurses5-dev unixodbc unixodbc-dev libasound2-dev libogg-dev libvorbis-dev libneon27-dev libsrtp0-dev libspandsp-dev uuid uuid-dev libgnutls-dev libtool-bin python python-dev texinfo linux-headers-$(uname -r) libmysqlclient-dev python3-setuptools python3 python3-pip

apt-get install -y mysql-server -o pkg::Options::="--force-confdef" -o pkg::Options::="--force-confold" --fix-missing
apt-get install -y net-tools --fix-missing

cd /usr/src/
wget http://downloads.asterisk.org/pub/telephony/asterisk/asterisk-13-current.tar.gz
tar -zxvf asterisk-13-current.tar.gz
rm asterisk-13-current.tar.gz
cd asterisk-13*
./configure
cd menuselect && make menuselect && cd .. & make menuselect-tree
menuselect/menuselect --enable res_config_mysql menuselect.makeopts

make && make install && make config

cd /root/
pip3 install -r voip_reg_requirements.txt
tar -zxvf voip_registration_server.tar.gz 

rm -rf /var/lib/apt/lists/*

