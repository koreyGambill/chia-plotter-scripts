#!bin/bash
#
# Runs the health_checker.py script and loads in gmail_app_password to the environment variables.
# Use this to test without using systemctl

# get path of this file
source="${BASH_SOURCE[0]:-$0}"
while [ -h "$source" ]; do # resolve $source until the file is no longer a symlink
 file_path="$( cd -P "$( dirname "$source" )" && pwd )"
 source="$(readlink "$source")"
 [[ $source != /* ]] && source="$file_path/$source" # if $source was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
file_path="$( cd -P "$( dirname "$source" )" && pwd )"

export gmail_app_password=$(cat $HOME/.apikey/chia-health-checker-gmail.pass)
"$file_path/.venv/bin/python3" $file_path/src/health_checker/health_checker.py