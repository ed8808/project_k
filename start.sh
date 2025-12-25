#!/bin/sh

export HOME=/home/ubuntu
cd /home/ubuntu/project_k

# Update yt-dlp to latest version
pip3 install --upgrade yt-dlp

# trap Ctrl-C to prevent breakout
trap '' INT

while true
do
    python3 /home/ubuntu/project_k/ktv.py
done
