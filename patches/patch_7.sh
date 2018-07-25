#!/usr/bin/env bash

echo "Applying patch 7..."

cp /home/pi/Way-Connect_Box/patches/patch_7/dnmasq.eth.conf /etc/
cp /home/pi/Way-Connect_Box/patches/patch_7/dnmasq.wlan.conf /etc/
cp /home/pi/Way-Connect_Box/patches/patch_7/hosts /etc/
cp /home/pi/Way-Connect_Box/patches/patch_7/w.club.conf /etc/nginx/sites-available/
