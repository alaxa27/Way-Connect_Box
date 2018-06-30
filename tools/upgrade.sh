#!/usr/bin/env bash

ROOTDIR="/home/pi"

if mkdir "$ROOTDIR/update.lock" 2>/dev/null; then
  if [ -f ${ROOTDIR}/way-box-update ]; then
    wget -O "$ROOTDIR/way-box-update.remote" https://raw.githubusercontent.com/alaxa27/Way-Connect_Box/master/way-box-update

    . ${ROOTDIR}/way-box-update
    CURRENT_VERSION=$VERSION
    . ${ROOTDIR}/way-box-update.remote
    REMOTE_VERSION=$VERSION

    if [ $REMOTE_VERSION -gt $CURRENT_VERSION ]; then
      # Install the upgrade
      cd "$ROOTDIR/Way-Connect_Box"
      git pull --rebase
      sh -c "$ROOTDIR/Way-Connect_Box/patch.sh"
      rm $ROOTDIR/way-box-update
      mv $ROOTDIR/way-box-update.remote $ROOTDIR/way-box-update
    fi
    $ROOTDIR/way-box-update.remote
  fi
  rmdir $ROOTDIR/update.lock
  reboot
fi
