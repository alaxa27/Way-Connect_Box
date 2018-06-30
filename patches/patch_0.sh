#!/usr/bin/env bash

echo "Applying patch 0..."
crontab -l > /home/pi/cron
echo "@reboot /home/pi/Way-Connect_Box/tools/upgrade.sh" >> /home/pi/cron
crontab /home/pi/cron
rm /home/pi/cron
