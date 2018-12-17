#!/bin/bash

IMAGE=$1
DEVICE=$2
BOOT_PARTITION=$3
MOUNT_POINT=$4

echo "Writing image to SD card..."
dd bs=4M if=$IMAGE of=$DEVICE status=progress
echo "Unmount boot partition..."
umount $BOOT_PARTITION
echo "Mounting boot partition on specified mount point..."
mount $BOOT_PARTITION $MOUNT_POINT
echo "Creating ssh file to allow ssh connection on first boot..."
touch $MOUNT_POINT/ssh.txt
echo "Unmounting boot partition..."
umount $BOOT_PARTITION
echo "Done."
