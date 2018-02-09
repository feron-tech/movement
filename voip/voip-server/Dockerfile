FROM ubuntu:16.04
LABEL maintainer="Feron Technologies <info@feron-tech.com>"
LABEL description="VoIP Probing Server for MONROE OC1 Movement Project"

COPY files/installation_procedure.sh /root/installation_procedure.sh
COPY files/voip_reg_requirements.txt /root/voip_reg_requirements.txt
COPY files/voip_registration_server.tar.gz /root/voip_registration_server.tar.gz
COPY files/startup.sh /root/startup.sh
COPY files/asterisk_conf/* /etc/asterisk/
COPY files/mysql_conf/asteriskrealtime.sql /tmp/
COPY files/asterisk_init/asterisk /etc/init.d/asterisk

COPY Dockerfile /root/

RUN /root/installation_procedure.sh

ENTRYPOINT ["/root/startup.sh"]

# BUILD : docker build -t ferontech/voip-server .
# RUN   : docker run --rm  --name voip-server -it --privileged --net=host ferontech/voip-server bash
