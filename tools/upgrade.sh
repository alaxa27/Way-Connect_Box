#!/usr/bin/env bash

ROOTDIR="."

if mkdir "$ROOTDIR/update.lock" 2>/dev/null; then
  if [ -f ${ROOTDIR}/way-box-update ]; then
    curl -o "$ROOTDIR/way-box-update.remote" -H 'Accept: application/vnd.github.v3.raw' -O -L 'https://api.github.com/repos/alaxa27/Way-Connect_Box/contents/way-box-update?ref=master'

    . ${ROOTDIR}/way-box-update
    CURRENT_VERSION=$VERSION
    CURRENT_PATCH=$PATCH
    . ${ROOTDIR}/way-box-update.remote
    REMOTE_VERSION=$VERSION
    REMOTE_PATCH=$PATCH

    if [ $REMOTE_VERSION -gt $CURRENT_VERSION ]; then
      # Install the upgrade
      cd "$ROOTDIR/Way-Connect_Box"
      git pull --rebase
      count=$CURRENT_PATCH
      while [ $count -lt $REMOTE_PATCH ]
      do
        sh -c "$ROOTDIR/Way-Connect_Box/patches/patch_$count.sh"
        ((count++))
      done
      rm $ROOTDIR/way-box-update
      mv $ROOTDIR/way-box-update.remote $ROOTDIR/way-box-update
      rmdir $ROOTDIR/update.lock
      sleep 1
      /sbin/shutdown -r now
    fi
    rm $ROOTDIR/way-box-update.remote
  fi
  rmdir $ROOTDIR/update.lock
fi
