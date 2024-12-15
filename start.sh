#!/bin/sh

export HOME=/home/ubuntu
cd /home/ubuntu/code/project_k

# trap Ctrl-C to prevent breakout
trap '' INT

while true
do
    python3 /home/ubuntu/code/project_k/ktv.py
done
