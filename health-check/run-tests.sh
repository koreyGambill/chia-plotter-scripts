#!bin/bash
#
# Runs the unit tests

# get path of this file
source="${BASH_SOURCE[0]:-$0}"
while [ -h "$source" ]; do # resolve $source until the file is no longer a symlink
 file_path="$( cd -P "$( dirname "$source" )" && pwd )"
 source="$(readlink "$source")"
 [[ $source != /* ]] && source="$file_path/$source" # if $source was a relative symlink, we need to resolve it relative to the path where the symlink file was located
done
file_path="$( cd -P "$( dirname "$source" )" && pwd )"
venv_python3="$file_path/.venv/bin/python3"

function print_help {
    echo "
        Purpose:
            Runs pytest unit tests in the test/ directory
        Usage: bash run-tests.sh [param1]
            -v    for verbose
    "
    exit 0
}

if [[ $1 == "-h" ]]; then
    print_help
fi

if [[ $1 == "-v" ]]; then
    set_debug="--log-cli-level=DEBUG"
    set_flag="-s"
fi

cd "$file_path"
"$venv_python3" -m "pytest" "$set_debug" "$set_flag"