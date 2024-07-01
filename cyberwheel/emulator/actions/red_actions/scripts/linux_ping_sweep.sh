#!/bin/bash

# This script executes a ping sweep in a linux/macos shell.
#
# Input Argruments: 
#     START_HOST - start ip value (e.g. 1)
#     END_HOST - end ip value (e.g. <=254)
#     SUBNET - subnet (e.g. 192.168.1)
#
# Returns: discovered ip address seperated by new line.

START_HOST=$1 # start sequence (e.g. 1)
STOP_HOST=$2 # end sequence (e.g. <=254)
SUBNET=$3 # e.g. 192.168.1

# Another method for ping sweep
#for i in {1..2}; do (ping -c 1 192.168.1.$i | grep "bytes from"); done

# MITRE ID T108
# Remote System Discover - sweep 
## added grep and cut to only show discovered IPs
for ip in $(seq $START_HOST $STOP_HOST); do ping -c 1 $SUBNET.$ip; [ $? -eq 0 ] && echo "$SUBNET.$ip UP" || :; done | grep "UP" | cut -d " " -f 1
