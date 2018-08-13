FROM ubuntu:16.04

# Setup app folder
WORKDIR /app

# Configure apt
RUN apt-get update && apt-get -y install \ 
    apt-utils \
    build-essential \
    software-properties-common \
    python3-software-properties \
    python3-setuptools \
    git \
    wget \
    expect \
    bc 

RUN add-apt-repository -y ppa:ubuntugis/ubuntugis-unstable \
    && apt-get update && apt-get -y install \ 
    gdal-bin \
    python-gdal

# Setup python3
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1 \
    && easy_install3 pip \
    && pip install \
        awscli \
        virtualenv

# --------- Place machine build layers before this line ---------

# Install snap toolbox
COPY config/app/install-snap.sh /app

RUN wget http://step.esa.int/downloads/6.0/installers/esa-snap_all_unix_6_0.sh \
    && chmod +x install-snap.sh \
    && ./install-snap.sh \
    && rm install-snap.sh \
    && rm esa-snap_all_unix_6_0.sh \
    && snap --nosplash --nogui --modules --update-all

# Configure snap toolbox
COPY config/app/snap/bin/gpt.vmoptions ./snap/bin

# Install snap toolbox scripts.
COPY /app/toolchain/scripts ./toolchain/scripts

# Copy toolchain config
COPY config/app/toolchain/scripts/JNCC_S1_GRD_configfile_v.1.1.sh ./toolchain/scripts

# Create processing paths
RUN mkdir -p /data/dem/ \
    && mkdir -p /data/sentinel/1/ \
    && mkdir /data/raw/ \
    && mkdir /data/states/ \
    && mkdir /data/processed/ \
    && mkdir /data/basket/

# Copy workflows
COPY /app/workflows ./workflows

# Copy workflow config
COPY config/app/workflows/luigi.cfg ./workflows
RUN chmod +r ./workflows/luigi.cfg

# Build virtual env
COPY config/app/workflows/install-venv.sh ./workflows
RUN chmod +x ./workflows/install-venv.sh \
    && ./workflows/install-venv.sh \
    && rm -f ./workflows/install-venv.sh

#Initialise startup script
COPY app/exec.sh ./
RUN chmod +rx /app/exec.sh

ENTRYPOINT ["/app/exec.sh"]