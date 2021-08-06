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

. $CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt

cd $CHIA_BLOCKCHAIN_HOME
. ./activate
cd -
cd $CHIA_BLOCKCHAIN_HOME/chia-blockchain-gui
npm run electron &
cd - # Returning to previous directory before running startGUI