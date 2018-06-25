apt-get update
apt-get upgrade
apt-get install -Y hostapd dnsmasq libmicrohttpd-dev python3 python3-dev python3-pip nginx-common nginx

cd nodogsplash/
make && make install
cd ../

cd middleware/
pip3 install -r requirements.txt
cd ../

cp -R config/* /etc/
ln -s /etc/nginx/sites-available/middleware.conf /etc/nginx/sites-enabled
