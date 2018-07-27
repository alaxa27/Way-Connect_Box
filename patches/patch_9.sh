#!/usr/bin/env bash

echo "Applying patch 9..."

ROOTDIR="/home/pi"

. ${ROOTDIR}/env
NEXT_MODE=$AP_MODE

if [ -z "$NEXT_MODE" ]
then
else
  NEXT_MODE="wlan"
fi

ln -sf ${ROOTDIR}/Way-Connect_Box/config/iptables.${NEXT_MODE}.ipv4.nat /etc/iptables.ipv4.nat
ln -sf ${ROOTDIR}/Way-Connect_Box/config/dnsmasq.${NEXT_MODE}.conf /etc/dnsmasq.conf
ln -sf ${ROOTDIR}/Way-Connect_Box/config/rc.${NEXT_MODE}.local /etc/rc.local
ln -sf ${ROOTDIR}/Way-Connect_Box/config/network/interfaces.${NEXT_MODE} /etc/network/interfaces
ln -sf ${ROOTDIR}/Way-Connect_Box/config/nodogsplash/nodogsplash.${NEXT_MODE}.conf
