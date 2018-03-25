FROM monroe/base
LABEL maintainer="Feron Technologies <info@feron-tech.com>"
LABEL description="Benchmarking Clients for MONROE OC1 Movement Project"

RUN apt-get update && apt-get install --no-install-recommends -y \
iputils-ping \
python-pip \
vlc-nox \
python-pcapy \
&& rm -rf /var/lib/apt/lists/* \
&& apt-get clean

RUN pip install pymongo

COPY files/ /opt/monroe/
COPY testfiles/jellyfish_50MB.mkv /opt/monroe/

ENTRYPOINT ["dumb-init", "--", "/bin/bash", "/opt/monroe/script.sh"]

# BUILD : docker build -t ferontech/bench-node .
# RUN   : docker run --rm -it  --name bench-node-cn -v ~/path/to/store/results:/monroe/results --privileged ferontech/bench-node
