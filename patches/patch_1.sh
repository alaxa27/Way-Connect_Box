#!/usr/bin/env bash

echo "Applying patch 1..."
crontab -l > /home/pi/cron
sed '$d'/home/pi/cron > /home/pi/cron.new
crontab /home/pi/cron.new
rm /home/pi/cro*
