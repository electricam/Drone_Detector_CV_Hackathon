#!/bin/bash

while true; do
    rsync -az --delete --timeout=10 ~/Documents/CV\ Hackathon/ Sam@raspberrypi.local:~/CV_Hackathon/
    sleep 5
done
