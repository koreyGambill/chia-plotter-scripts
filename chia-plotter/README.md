# Chia Installation

# Install Chia Blockchain Code
If you don't install this at ~/chia-blockchain, then you should update the conf/chia-plotter-config.txt with your directory of installation
https://github.com/Chia-Network/chia-blockchain/wiki/INSTALL#ubuntudebian

# General Info
The install script does a few things:  

**Adds alias'**  
It adds the alias' chiaStartPlotter, chiaStopPlotter, chiaStartGUI, and chiaStartPlotterGradually.  
You can run those in a terminal from anywhere to manage the plotter.  

**Adds cronjob**   
It adds the cronjob for you that will run the chiaPlotter every 5 minutes.  
The logs from the cronjob will be output to logs/cronjob.log   

**Pauses chiaPlotter.sh**  
It will also pause the chiaPlotter for now so that the runs triggered by cronjob don't actually run.  
The chiaPlotter runs if the RUN_SCRIPT="true", so the install script sets it to false. This is set in conf/chia-plotter-config.txt.

**It's re-runnable**  
The install script should be idempotent - meaning that it deletes the cronjob task and alias' that it creates before it re-creates them. You can run the install over and over with no consequence. Also, if you move your chia-plotter-scripts folder, you can re-run the install script to get the alias' and cronjob pointing at the right spots again.

# Run install Script
Run the script install.sh with a source command like
`. install.sh`
You can run it with `bash install.sh`, but it won't allow the variables set to be available until you reload your terminal session


# Configuring chia-plotter-config
First, make a copy of conf/chia-plotter-config-example.txt, and name it chia-plotter-config.txt. Then configure it.

Right now, it takes 256.6 GB temp space to create a plot. That means a 1tb SSD can do 3 temp files. a 4tb SSD in a raid0 should be able to do 15.5 temp files. I think RAID0 wastes some space, but you should be able to get away with 15 or 14.  

I would recommend using at least 4000 for the memory.  

3 threads per plot is best. It uses up to 3 (sometimes barely more than 3) in phase one. All other phases are single threaded.  

Figure out how many to run by maximizing use of threads in phase 1 while also maximizing total plots running. If you have an 8 core CPU, you have 16 threads. This process is also a bit of an art because you can overallocate threads and the processes will starve each other a bit, but maybe it's faster anyways.  

Lastly, set your final directories. It's best if you can set those to be equal to the number of plots in phase 1 because it will avoid bottlenecking on the transfer in phase 4. Otherwise, consider using the startPlotterGradually script, but you'll have to configure it for the number that you want and how long you want the sleep to be.

The final file is 108.8 GB  
The transfer from Temp Directory to Final Directory in phase 4 takes about 15 minutes.  
110 files fit on a 12Tb drive formatted to `sudo mkfs.ext4 -m 0 -T largefile4 -L <driveLabel> /dev/<mountpoint>`  

# Raid Array (SSD Temp Drives)
digital ocean has a really good guide. These are snippets pulled from their guide.  
An easy way to create and delete these is copy-pasting the commands in bulk from bin/createRaidArray.sh and bin/deleteRaidArray.sh into a terminal after editing a couple values

## Create Raid Array

`sudo install mdadm`
`sudo mdadm --create --verbose /dev/md0 --level=0 --chunk=64 --raid-devices=4 /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1 /dev/nvme3n1` - creates raid array

`cat /proc/mdstat` - verifies array exists

`sudo apt install xfsprogs` - install xfssprogs for the mkfs.xfs command

`sudo mkfs.xfs -f /dev/md0` - formats raid array with xfs
`sudo mkdir -p /mnt/raidDrive` - make the directory you want to mount the raid array to
`sudo chmod 777 /mnt/raidDrive` - edit it's permissions
`sudo mount /dev/md0 /mnt/raidDrive` - mount it

`df -h -x devtmpfs -x tmpfs` - check that it has the space you'd expect

`sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf` - Add the raid array to your mdadm.conf file (idk what this does)
`sudo update-initramfs -u` - not sure what this does

`echo '/dev/md0 /mnt/raidDrive xfs defaults,nofail,discard 0 0' | sudo tee -a /etc/fstab` - Auto mount this in the future by adding the mount config to your fstab file

## Delete Raid Array (if needed)

`cat /proc/mdstat` - check where things are set
`sudo umount /dev/md0`  
`sudo mdadm --stop /dev/md0`  
`sudo mdadm --remove /dev/md0`  
`sudo mdadm --zero-superblock /dev/nvme0n1`  
`sudo mdadm --zero-superblock /dev/nvme1n1`  
`sudo mdadm --zero-superblock /dev/nvme2n1`  
`sudo vim /etc/fstab`  
`sudo vim /etc/mdadm/mdadm.conf`  
`sudo update-initramfs -u`  

# Add New Destination Drives

## Format Destination Drives
First you want to format the drive like this:

`sudo mkfs.ext4 -m 0 -T largefile4 -L <driveLabel> /dev/<mountpoint>`  

## Add to Plotter
Add new drives to the finalDirs variable in conf/chia-plotter-config.txt
Then run the addNewFinalDirs.sh file. It will create the plots directory and add the right permissions.
Now you should be ready to plot to the hard drives

## Testing new Destination Drives
If you want to, you can run a speed test on your drives. This is a good idea if you get a new enclosure.

`TEST_DIR=/media/$(whoami)/farm30/fiotest && sudo mkdir -p $TEST_DIR`  

`sudo fio --name=write_throughput --directory=$TEST_DIR --numjobs=8 --size=1G --time_based --runtime=30s --ramp_time=2s --ioengine=libaio --direct=1G --verify=0 --bs=1M --iodepth=64 --rw=write --group_reporting=1`  

`sudo rm -rf $TEST_DIR`  

## Testing SSD Drives (Temp Drives)
You can run the bin/testSSD.sh script, but it does the mounting and unmounting for you. Don't do this except on fresh SSDs.
`DRIVE=nvme0n1`  
`sudo mkdir -p /mnt/$DRIVE`  
`sudo chmod 777 /mnt/$DRIVE`  
`sudo mkfs.xfs -f /dev/nvme2n1`  
`sudo mount /dev/nvme2n1 /mnt/nvme2`  
`TEST_DIR=/mnt/$DRIVE/fiotest && mkdir -p $TEST_DIR`  
`fio --name=write_throughput --directory=$TEST_DIR --numjobs=8 --size=1G --time_based --runtime=30s --ramp_time=2s --ioengine=libaio --direct=1G --verify=0 --bs=1M --iodepth=64 --rw=write --group_reporting=1`  

# Restarting Chia Plotter
If you want to restart chia, do these steps

1) Stop new chia runs. You can do this by running the stopPlotter.sh script in the ~/chia-plotter-scripts folder

2) Kill running plots in System Montor. You can find them by searching /farm or whatever your harddrives are named

3) Clear running files from ~/chia-plotter-scripts/logs/running/ 
Clear through terminal: type  
`rm ~/chia-plotter-scripts/logs/running/*` - To delete the files  
`ls ~/chia-plotter-scripts/logs/running/` - To check they are deleted  

4) Clear temp files in /mnt/raidDrive/
Clear through terminal: type   
`rm ~/mnt/raidDrive/*` - To delete the files  
`ls ~/mnt/raidDrive/` - To check they are deleted  

5) Start new chia runs. You can do this by running  
`chiaPlotterStart` - an alias added by the install script  
or clicking into the chia-plotter-scripts and running startPlotter.sh. You'll have to enable running scripts through your filesystem.


# Cronjob Info
`crontab -e` - Bring up your cronjob config file for editing  
`crontab -l` - Lists your current cronjob configuration  
The install script will insert something like this in your crontab config depending on where your directory is  
`*/1 * * * * /home/<username>/chia-plotter-scripts/bin/chiaPlotter.sh >> /home/<username>/chia-plotter-scripts/logs/cronjob.log 2>&1`