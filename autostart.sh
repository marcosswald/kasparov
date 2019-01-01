#!/bin/bash

# start noip daemon
sudo noip2

# start flask server
cd /home/pi/kasparov
python3 kasparov.py

# shut down system
sudo poweroff