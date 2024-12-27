# Convert and playback  YouTUBE video to separated music and separated vocal

## Installation

pip install -r requirements.txt

sudo cp ktv.service /etc/systemd/system/
sudo systemctl enable ktv.service
sudo systemctl start ktv.service

## System setup
1. enable auto logon
2. access local web server at port 3000

## Docker build
sudo docker build --tag project_k .

## Docker run
export XDG_RUNTIME_DIR=/run/user/1000

check if echo $XDG_RUNTIME_DIR returns /run/user/1000

sudo docker run \ 
--rm -d \
--device /dev/snd \
-e DISPLAY=$DISPLAY \ 
-e XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR \
-v /run/user/1000/pulse:/run/user/1000/pulse \
-v /tmp/.X11-unix/:/tmp/.X11-unix \
-v $HOME/project_k/output:/project_k/output \
-v $HOME/project_k/data:/project_k/data \
-p 3000:3000 \
project_k

local directory $HOME/project_k shall contain docker volume mount folders
access local web server at port 3000
