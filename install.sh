apt update
apt -y upgrade
apt install -y hostapd ipset dnsmasq libmicrohttpd-dev python3 python3-dev python3-pip nginx-common nginx

cd nodogsplash/
make && make install
cd ../

cd middleware/
pip3 install -r requirements.txt
cd ../

cp -R config/* /etc/
cp -R w.zone/ /var/www/
ln -s /etc/nginx/sites-available/middleware.conf /etc/nginx/sites-enabled
ln -s /etc/nginx/sites-available/w.zone.conf /etc/nginx/sites-enabled
systemctl daemon-reload
systemctl enable middleware

# Cronjob that checks for upgrades
echo "*/5 * * * * /home/pi/Way-Connect_Box/middleware/recurrent_tasks.py" >> cron
crontab cron
rm cron

cp env ../
cp keys ../

git config --global user.email "a@a.a"
git config --global user.name "a"
