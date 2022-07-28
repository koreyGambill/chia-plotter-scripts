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

sed -i 's/RUN_SCRIPT="false"/RUN_SCRIPT="true"/g' "$CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt"
notify-send "Started Script at $CHIA_PLOTTER_SCRIPTS_HOME/conf/chia-plotter-config.txt"
