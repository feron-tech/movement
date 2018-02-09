FROM monroe/base
LABEL maintainer="Feron Technologies <info@feron-tech.com>"
LABEL description="VoIP Probing Client for MONROE OC1 Movement Project"

RUN apt-get update -y \
&& apt-get install --no-install-recommends -y \
python-pip \
linphone \
netcat-openbsd \
python-pcapy \
&& apt-get clean autoclean && apt-get autoremove -y && rm -rf var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install \
--upgrade setuptools \
dpkt \
numpy \
pyping \
pymongo

EXPOSE 1883

COPY files/ /opt/monroe/

COPY Dockerfile /root/

ENTRYPOINT dumb-init -- /bin/bash /opt/monroe/run_main.sh


# BUILD : docker build -t ferontech/voip-node .
# RUN   : docker run --rm -it  --name voip-node-cn -v ~/path/to/store/results:/monroe/results --privileged ferontech/voip-node
