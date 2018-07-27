#!/usr/bin/env bash

echo "Applying patch 8..."

cp /home/pi/Way-Connect_Box/patches/patch_8/hostapd.conf /etc/hostapd/
apt-get install -y jq
