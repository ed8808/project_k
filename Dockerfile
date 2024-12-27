# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

WORKDIR /project_k

RUN apt-get -y update && apt-get -y upgrade
RUN apt-get -y install mpv libmpv-dev
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "ktv" ]
