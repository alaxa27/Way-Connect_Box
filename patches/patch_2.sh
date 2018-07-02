#!/usr/bin/env bash

echo "Applying patch 2..."

cp /home/pi/Way-Connect_Box/config/nodogsplash/htdocs/splash.html /etc/nodogsplash/htdocs
cp /home/pi/Way-Connect_Box/config/hosts /etc/
cp -R /home/pi/Way-Connect_Box/config/nginx /etc/
cp -R /home/pi/Way-Connect_Box/wc.com/ /var/www/
ln -s /etc/nginx/sites-available/wc.com.conf /etc/nginx/sites-enabled
