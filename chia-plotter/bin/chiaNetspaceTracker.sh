#!/bin/bash
set -euxo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do # resolve $SOURCE until the file is no longer a symlink
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE" # if $SOURCE was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
CHIA_PLOTTER_SCRIPTS_HOME=`dirname $DIR`

# Should be ran on a pc that already has the full node synced to the blockchain
# */10 * * * * $HOME/chia-plotter-scripts/chiaNetspaceTracker.sh

cd ~/chia-blockchain
. ./activate
timestamp=`date +%m/%d/%Y\ %H:%M:%S`
echo `chia show -s | grep "Estimated network space" | sed "s#Estimated network space#$timestamp#g"` | tee -a $CHIA_PLOTTER_SCRIPTS_HOME/logs/netspace.txt
deactivate
