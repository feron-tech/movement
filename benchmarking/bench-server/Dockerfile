FROM ubuntu:14.04
LABEL maintainer="Feron Technologies <info@feron-tech.com>"
LABEL description="Benchmarking Server Components for MONROE OC1 Movement Project"

RUN apt-get update && apt-get install --no-install-recommends -y \
wget \
unzip \
apache2 \
php5 php5-mysql php5-mcrypt php5-gd libapache2-mod-php5 \
apache2-utils \
iperf3 \
&& apt-get clean

# speedtest
RUN wget http://c.speedtest.net/mini/mini.zip
RUN unzip mini.zip
RUN rm -f mini.zip
RUN mv mini/ /var/www/html/
RUN mv /var/www/html/mini/index-php.html  /var/www/html/mini/index.html

# http download file
COPY conf/jellyfish_50MB.mkv /var/www/html/

# http upload file
RUN cd /etc/apache2/mods-enabled
RUN ln -s ../mods-available/cgi.load
RUN htpasswd -bc /usr/local/apache2_passwords testuser testuser
COPY conf/serve-cgi-bin.conf /etc/apache2/conf-enabled/
COPY conf/save_video.py /usr/lib/cgi-bin/

#iperf3
COPY conf/multi_iperf3_server.sh /home/


ENTRYPOINT \
echo "ServerName localhost" >> /etc/apache2/apache2.conf && \
service apache2 restart && \
/home/multi_iperf3_server.sh && \
/bin/bash

# BUILD : docker build -t ferontech/bench-server .
# RUN   : docker run --rm -idt --name bench-server-cn --privileged -p 8081:80 -p 8201-8204:5201-5204 ferontech/bench-server
