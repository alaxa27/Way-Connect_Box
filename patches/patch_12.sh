#!/usr/bin/env bash

echo "Applying patch 12..."

ROOTDIR="/home/pi"
. ${ROOTDIR}/env
NEXT_MODE=$AP_MODE
ln -sf ${ROOTDIR}/Way-Connect_Box/config/network/interfaces.${NEXT_MODE} /etc/network/interfaces
