#!/usr/bin/env bash

echo "Applying patch 10..."

ROOTDIR="/home/pi"

. ${ROOTDIR}/env
NEXT_MODE=$AP_MODE

if [ -z "$NEXT_MODE" ]
then
  NEXT_MODE="wlan"
else
  echo "AP mode configured already."
fi

ln -sf ${ROOTDIR}/Way-Connect_Box/config/nodogsplash/nodogsplash.${NEXT_MODE}.conf /etc/network/nodogsplash
