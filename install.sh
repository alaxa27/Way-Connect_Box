apt-get update
apt-get upgrade
apt-get install -Y hostapd dnsmasq libmicrohttpd-dev python3 python3-dev python3-pip nginx

cd nodogsplash/
make && make install
cd ../

cp -R config/* /etc/
ln -s /etc/nginx/sites-available/middleware /etc/nginx/sites-enabled
