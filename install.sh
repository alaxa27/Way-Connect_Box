#!/bin/bash

apt update
apt -y upgrade
apt install -y git
apt install -y hostapd ipset dnsmasq libmicrohttpd-dev nginx-common nginx
apt install -y  build-essential tk-dev libncurses5-dev libncursesw5-dev\
    libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev\
    libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev 
apt install -y rabbitmq-server redis-server
apt install -y monit

wget https://www.python.org/ftp/python/3.7.1/Python-3.7.1.tar.xz
tar xf Python-3.7.1.tar.xz
cd Python-3.7.1
./configure
make -j 4
make altinstall
cd ../
wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py
python3.7 get-pip.py


git clone https://github.com/alaxa27/Way-Connect_Box.git
cd Way-Connect_Box

cd nodogsplash/
make && make install
cd ../

cd middleware/
pip3.7 install -r requirements.txt
cd ../

# This is done at SD card writing
#cp eth/config.txt /boot
cp -R w.zone/ /var/www/
systemctl daemon-reload
systemctl disable dhcpcd
systemctl enable networking

# Cronjob that checks for upgrades
echo "*/1 * * * * /usr/local/bin/python3.7 /home/pi/Way-Connect_Box/middleware/recurrent_tasks.py" >> cron
crontab cron
rm cron

cp env ../

echo "API_KEY=\"${1}\"
API_SECRET=\"${2}\"" > /home/pi/keys

git config --global user.email "a@a.a"
git config --global user.name "a"


cp -R config/* /etc/
systemctl daemon-reload
systemctl enable ngrok hostapd middleware nginx nodogsplash nameko
mkdir -p /var/nginx/cache
/home/pi/Way-Connect_Box/middleware/recurrent_tasks.py
