#!/usr/bin/env bash

echo "Applying patch..."
crontab -l > /home/pi/cron
echo "@reboot /home/pi/Way-Connect_Box/tools/upgrade.sh" >> cron
crontab /home/pi/cron
rm /home/pi/cron
