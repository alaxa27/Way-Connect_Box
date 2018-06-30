#!/usr/bin/env bash

echo "Applying patch 0..."

echo "0 5 * * * /home/pi/Way-Connect_Box/tools/upgrade.sh" >> cron
crontab cron
rm cron
