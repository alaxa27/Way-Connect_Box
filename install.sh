apt-get update
apt-get upgrade
apt-get install -y hostapd dnsmasq libmicrohttpd-dev python3 python3-dev python3-pip nginx

cd nodogsplash/
make && make install
cd ../

ln -s /etc/nginx/sites-available/middleware /etc/nginx/sites-enabled
cp -R config/* /etc/
