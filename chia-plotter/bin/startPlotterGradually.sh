#!/bin/bash
set +eux

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
CHIA_PLOTTER_SCRIPTS_HOME=`dirname $DIR`

# Read out config file
. "$CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt"

# Set desired number of plots to 0 and start the plotter
sed -i 's/desiredNumberOfPlotsInPhase1=[0-9]/desiredNumberOfPlotsInPhase1=0/g' "$CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt"
bash "$CHIA_PLOTTER_SCRIPTS_HOME/bin/startPlotter.sh"

# Ramp up the desiredNumberOfPlotsInPhase1 to whatever was set in conf/chia-plotter-config.txt for rampSlowlyTo.
for (( i=$rampSlowlyFrom; i<=$rampSlowlyTo; i++ ))
do  
   echo "Setting desiredNumberOfPlotsInPhase1 to $i"
   sed -i "s/desiredNumberOfPlotsInPhase1=[0-9]/desiredNumberOfPlotsInPhase1=${i}/" "$CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt"
   sleep $secondsBetween
done