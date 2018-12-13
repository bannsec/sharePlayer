
# sudo docker run -it --rm --name shareplayer --network=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix/ shareplayer

FROM ubuntu:bionic

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get dist-upgrade -y && apt-get install -y python3 python3-pip stunnel mplayer locales && \
    useradd -m shareplayer && mkdir -p /opt/sharePlayer && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && locale-gen

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

WORKDIR /opt/sharePlayer

COPY . .
RUN pip3 install -e .[dev]

USER shareplayer
WORKDIR /home/shareplayer

CMD ["/bin/bash", "-c", "sharePlayer"]
