FROM python:3.11.9-bullseye

WORKDIR /app

COPY requirements.txt requirements.txt
COPY rules.json /rules.json

ENV VERSION=v4.34.1
ENV BINARY=yq_linux_amd64
RUN apt update -y
# RUN apt install yq -y
# RUN apt install python3-pip -y
RUN pip3 install --verbose -r requirements.txt
RUN apt install wget -y
RUN wget https://github.com/mikefarah/yq/releases/download/${VERSION}/${BINARY}.tar.gz -O - |\
  tar xz && mv ${BINARY} /usr/bin/yq

COPY package/bin /app/bin
COPY package/linter /app/linter
COPY package/setup.py /app/setup.py

RUN python3 setup.py install
