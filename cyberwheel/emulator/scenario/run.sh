#!/bin/bash

# This script starts the CyberWheel experiement in FireWheel.
# The configuration file must be included when executing the script:
#
#                ./run <config_name>
#
# The available configurations can be found in the ./configs folder.

if [[ $# -eq 0 ]]; then
    echo "Missing config name as argrument. See './configs' folder and use './run <config_name>.yaml'"
    exit 1
fi

if [[ $# -gt 1 ]]; then
    echo "Invalid number of agruments. See './configs' folder and use './run <config_name>.yaml'"
    exit 1
fi

file=$1

if [ ! -f "configs/$file" ]; then
    echo "Configuration file not found in 'configs' folder. Ensure file exist and that '.yaml' is included in the name."
    exit 1
fi

export NETWORK_CONFIG=$1
echo "exported NETWORK_CONFIG=$NETWORK_CONFIG"

echo "Launching firewheel experiment..."
firewheel experiment -f cyberwheel.topology control_network minimega.launch
