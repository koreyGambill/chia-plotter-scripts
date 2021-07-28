#!bin/bash
#
# Runs the flask web server

# get path of this file
source="${BASH_SOURCE[0]:-$0}"
while [ -h "$source" ]; do # resolve $source until the file is no longer a symlink
 file_path="$( cd -P "$( dirname "$source" )" && pwd )"
 source="$(readlink "$source")"
 [[ $source != /* ]] && source="$file_path/$source" # if $source was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
file_path="$( cd -P "$( dirname "$source" )" && pwd )"

"$file_path/health-check-env/bin/python3" $file_path/src/health_check_server/app.py