#!/usr/bin/env bash

echo "Applying patch 6..."

echo "AP_MODE=\"wlan\"" > /home/pi/env

cp /home/pi/Way-Connect_Box/patches/patch_6/config.txt /boot/
cp /home/pi/Way-Connect_Box/patches/patch_6/rc.local /etc/
