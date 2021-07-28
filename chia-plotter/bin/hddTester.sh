#!/bin/bash
set +eux

apt update
apt install -y fio

# set TEST_DIR as path to hard drive:
# /media/<username>/farm30/fiotest

TEST_DIR=/media/$(whoami)/farm30/fiotest
mkdir -p $TEST_DIR

# script fio-test-log

# create files

touch /tmp/fio-write-throughput
touch /tmp/fio-write-iops
touch /tmp/fio-read-throughput
touch /tmp/fio-read-iops

# Write Throughput

fio --name=write_throughput --directory=$TEST_DIR --numjobs=8 --size=1G --time_based --runtime=60s --ramp_time=2s --ioengine=libaio --direct=1G --verify=0 --bs=1M --iodepth=64 --rw=write --group_reporting=1 >> /tmp/fio-write-throughput

# Write IOPS

fio --name=write_iops --directory=$TEST_DIR --size=1G --time_based --runtime=60s --ramp_time=2s --ioengine=libaio --direct=1 --verify=0 --bs=4K --iodepth=64 --rw=randwrite --group_reporting=1 >> /tmp/fio-write-iops



# Read Throughput

fio --name=read_throughput --directory=$TEST_DIR --numjobs=8 --size=1G --time_based --runtime=60s --ramp_time=2s --ioengine=libaio --direct=1G --verify=0 --bs=1M --iodepth=64 --rw=read --group_reporting=1 >> /tmp/fio-read-throughput


# Read IOPS

fio --name=read_iops --directory=$TEST_DIR --size=1G --time_based --runtime=60s --ramp_time=2s --ioengine=libaio --direct=1 --verify=0 --bs=4K --iodepth=64 --rw=randread --group_reporting=1 >> /tmp/fio-read-iops
# exit
