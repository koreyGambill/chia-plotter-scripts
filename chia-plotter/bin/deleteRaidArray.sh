#!/bin/bash
set +eux 

cat /proc/mdstat
sudo umount /dev/md0
sudo mdadm --stop /dev/md0
sudo mdadm --remove /dev/md0
sudo mdadm --zero-superblock /dev/nvme0n1
sudo mdadm --zero-superblock /dev/nvme1n1
sudo mdadm --zero-superblock /dev/nvme2n1
sudo mdadm --zero-superblock /dev/nvme3n1
sudo mdadm --zero-superblock /dev/nvme4n1
# Paste these individually
sudo vim /etc/fstab # Delete the reference to the array
sudo vim /etc/mdadm/mdadm.conf # Delete the reference to the array
sudo update-initramfs -u
