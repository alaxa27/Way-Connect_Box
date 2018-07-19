#!/usr/bin/env bash

ROOTDIR="/home/pi"

if [ -f ${ROOTDIR}/env ]; then
  . ${ROOTDIR}/env
  NEXT_MODE=$AP_MODE

  if [ ! -f ${ROOTDIR}/ap ]; then
    touch ${ROOTDIR}/ap
    echo "AP_MODE=\"$NEXT_MODE\"" >> ${ROOTDIR}/ap
  fi

  . ${ROOTDIR}/ap
  CURRENT_MODE=$AP_MODE

  if [ $CURRENT_MODE != $NEXT_MODE ]; then
    # Install the upgrade

    ln -sf ${ROOTDIR}/Way-Connect_Box/config/iptables.${NEXT_MODE}.ipv4.nat /etc/iptables.ipv4.nat
    ln -sf ${ROOTDIR}/Way-Connect_Box/config/dnsmasq.${NEXT_MODE}.conf /etc/dnsmasq.conf
    ln -sf ${ROOTDIR}/Way-Connect_Box/config/rc.${NEXT_MODE}.local /etc/rc.local
    ln -sf ${ROOTDIR}/Way-Connect_Box/config/network/interfaces.${NEXT_MODE} /etc/network/interfaces
    ln -sf ${ROOTDIR}/Way-Connect_Box/config/nodogsplash/nodogsplash.${NEXT_MODE}.conf /etc/nodogsplash/nodogsplash.conf

    echo "AP_MODE=\"$NEXT_MODE\"" > ${ROOTDIR}/ap
    sleep 1
    /sbin/shutdown -r now
  fi
fi
