#!/bin/bash
set +eux

if [[ $# -eq 1 ]]; then

    # Mount Drive and Test
    DRIVE=$1 # Should be like nvme0n1

    if [[ $DRIVE =~ ^nvme[0-9]n1$ ]]; then
        echo "Running tests on the drive: dev/$DRIVE"
        sudo mkdir -p /mnt/$DRIVE
        sudo chmod 777 /mnt/$DRIVE
        sudo mkfs.xfs -f /dev/$DRIVE
        sudo mount /dev/$DRIVE /mnt/$DRIVE
        TEST_DIR=/mnt/$DRIVE/fiotest
        sudo mkdir -p $TEST_DIR
        sudo chmod 777 $TEST_DIR
        sudo fio --name=write_throughput --directory=$TEST_DIR --numjobs=8 --size=1G --time_based --runtime=40s --ramp_time=2s --ioengine=libaio --direct=1G --verify=0 --bs=1M --iodepth=64 --rw=write --group_reporting=1
        
        # Cleanup
        sudo umount /dev/$DRIVE
        sudo rm -rf /mnt/$DRIVE
    else
        echo "This script is dangerous to do on HDDs. Strictly matching names like 'nvme0n1'"
    fi
else
    echo "Cannot run without a drive"
fi
