#!/usr/bin/env bash

echo "Applying patch 8..."

rm /var/lib/dpkg/info/pi-bluetooth*
apt-get install --reinstall pi-bluetooth
apt-get install -y jq
cp /home/pi/Way-Connect_Box/patches/patch_8/hostapd.conf /etc/hostapd/
