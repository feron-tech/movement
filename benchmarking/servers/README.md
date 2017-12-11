### The Server-Side Components of MOVEMENT Benchmarking Tests

#### Introduction
This sub-project contains detailed instructions for loading the necessary server-side components in order to run the various MOVEMENT benchmarking clients.
Although each server could be loaded and configured to operate in a standalone mode in a typical Linux host, here we propose a method to prepare a single Docker image containing all the components installed and pre-configured. This significantly eases the server deployment, as it resorts to the execution of a single container.

#### Contents
The MOVEMENT server-side container includes:
* An ```iperf3``` server, and in particular 4 instances running in ports 5201-5204, enabling iperf3 TCP/UDP testing.
* A local ```Speedtest``` server, enabling speedtest execution in a private server, based on instructions found [here](http://www.tecmint.com/speedtest-mini-server-to-test-bandwidth-speed/).
* An HTTP Apache Web-Server hosting a large file (50 MB size) for performing HTTP file download tests (using the ```curl``` package).
* A web application written in CGI/Python and hosted in the same Apache Web-Sever, where CGI has been configured appropriately, enabling HTTP file upload tests (using the ```curl``` package).

#### Preparing the Image
The image is based on the ```Ubuntu Trusty``` linux distribution:
```
FROM ubuntu:14.04
```

Initially a set of necessary packages are installed:
```
RUN apt-get update && apt-get install --no-install-recommends -y \
wget \
unzip \
apache2 \
php5 php5-mysql php5-mcrypt php5-gd libapache2-mod-php5 \
apache2-utils \
iperf3 \
&& apt-get clean
```

Then each component is configured, starting with Private Speedtest Server. The procedure includes the retrieval of the neccessary files and their placement to the Apache default shared path.
```
RUN wget http://c.speedtest.net/mini/mini.zip
RUN unzip mini.zip
RUN rm -f mini.zip
RUN mv mini/ /var/www/html/
RUN mv /var/www/html/mini/index-php.html  /var/www/html/mini/index.html
```

Next, the file used for HTTP download tests is copied to the same public folder:
```
COPY conf/jellyfish_50MB.mkv /var/www/html/
```

For HTTP upload we need first to enable CGI scripts in Apache, then copy the server-side script that performs the dummy actions for file uploading, and finally create security credentials for allowing file uploading to specific users (in this example a user called ```testmonroeuser``` with the same password as the login name is created)
```
RUN cd /etc/apache2/mods-enabled
RUN ln -s ../mods-available/cgi.load
RUN htpasswd -bc /usr/local/apache2_passwords testmonroeuser testmonroeuser
COPY conf/serve-cgi-bin.conf /etc/apache2/conf-enabled/
COPY conf/save_file.py /usr/lib/cgi-bin/
```
Finally a script loading the 4 parallel ```iperf3``` servers is transferred to the container user-space:
```
COPY conf/multi_iperf3_server.sh /home/
```

At container startup the following actions are performed:
* Configuration for Apache2 Web-Server hostname
* Start up the Web-Server
* Start up the various iperf3 server instances

```
ENTRYPOINT echo "ServerName localhost" >> /etc/apache2/apache2.conf && service apache2 restart && /home/multi_iperf3_server.sh && /bin/bash
```

#### Loading the Container
The container is created under a single command (assuming ```servers``` is the name of the Docker image):
```
docker run --rm -idt --name servercn --privileged -p 8081:80 -p 8201-8204:5201-5204 servers
```
Notice that we are using non-default ports for HTTP and iperf3 to avoid conflict with possible host server instances running in the same machine. These ports should be configuted appropriately at the clients side.
