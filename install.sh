apt-get update
apt-get -y upgrade
apt-get install -y hostapd ipset dnsmasq libmicrohttpd-dev python3 python3-dev python3-pip nginx-common nginx

cd nodogsplash/
make && make install
cd ../

cd middleware/
pip3 install -r requirements.txt
cd ../

cp -R config/* /etc/
cp -R w.club/ /var/www/
ln -s /etc/nginx/sites-available/middleware.conf /etc/nginx/sites-enabled
ln -s /etc/nginx/sites-available/wc.com.conf /etc/nginx/sites-enabled
systemctl daemon-reload
systemctl enable middleware

# Cronjob that checks for upgrades
echo "0 5 * * * /home/pi/Way-Connect_Box/tools/upgrade.sh" >> cron
crontab cron
rm cron
cp way-box-update ../

cp env ../

git config --global user.email "a@a.a"
git config --global user.name "a"
