apt update
apt -y upgrade
apt install -y hostapd ipset dnsmasq libmicrohttpd-dev nginx-common nginx
apt install -y  build-essential tk-dev libncurses5-dev libncursesw5-dev\
    libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev\
    libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev 

cd ../
wget https://www.python.org/ftp/python/3.7.1/Python-3.7.1.tar.xz
tar xf Python-3.7.1.tar.xz
cd Python-3.7.1
./configure
make -j 4
make altinstall
cd ../
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python3.7 get-pip.py
cd Way-Connect_Box

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


