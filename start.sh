#!/bin/sh

export HOME=/home/ubuntu
cd /home/ubuntu/project_k

# trap Ctrl-C to prevent breakout
trap '' INT

while true
do
    python3 /home/ubuntu/project_k/ktv.py
done
