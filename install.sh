apt-get install -y hostapd dnsmasq python3 python3-dev python3-pip nginx

ln -s /etc/nginx/sites-available/middleware /etc/nginx/sites-enabled
cp -R config/* /etc/
