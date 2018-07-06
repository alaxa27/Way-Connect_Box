#!/usr/bin/env bash

echo "Applying patch 4..."

cp /home/pi/Way-Connect_Box/config/dnsmasq.conf /etc/
cp /home/pi/Way-Connect_Box/config/hosts /etc/
cp -R /home/pi/Way-Connect_Box/config/nginx /etc/
cp -R /home/pi/Way-Connect_Box/w.club/ /var/www/
rmdir /var/www/wc.com
rm /etc/nginx/sites-available/wc.com.conf
rm /etc/nginx/sites-enabled/wc.com.conf
ln -s /etc/nginx/sites-available/w.club.conf /etc/nginx/sites-enabled
