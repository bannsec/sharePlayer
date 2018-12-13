
# sudo docker run -it --rm --name shareplayer --network=host -e DISPLAY=$DISPLAY -v /tmp/.X11-unix/:/tmp/.X11-unix/ shareplayer

FROM ubuntu:bionic

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get dist-upgrade -y && apt-get install -y python3 python3-pip stunnel mplayer && \
    useradd -m shareplayer && mkdir -p /opt/sharePlayer

WORKDIR /opt/sharePlayer

COPY . .
RUN pip3 install -e .

USER shareplayer
WORKDIR /home/shareplayer

CMD sharePlayer
