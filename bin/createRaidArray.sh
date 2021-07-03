#!/bin/bash
set +eux 

# Edit the sudo mdadm command, then copy-paste everything

sudo apt install mdadm
sudo mdadm --create --verbose /dev/md0 --level=0 --chunk=64 --raid-devices=4 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme4n1    # creates raid array
cat /proc/mdstat    # verifies array exists
sudo apt install xfsprogs    # install xfssprogs for the mkfs.xfs command
sudo mkfs.xfs -f /dev/md0    # formats raid array with xfs
sudo mkdir -p /mnt/raidDrive    # make the directory you want to mount the raid array to
sudo chmod 777 /mnt/raidDrive    # edit it's permissions
sudo mount /dev/md0 /mnt/raidDrive    # mount it
df -h -x devtmpfs -x tmpfs    # check that it has the space you'd expect
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf    # Add the raid array to your mdadm.conf file (idk what this does)
sudo update-initramfs -u    # not sure what this does
echo '/dev/md0 /mnt/raidDrive xfs defaults,nofail,discard 0 0' | sudo tee -a /etc/fstab    # Auto mount this in the future by adding the mount config to your fstab file
