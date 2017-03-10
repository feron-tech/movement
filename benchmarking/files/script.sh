#!/bin/bash
# Main script called when container starts

python /opt/monroe/run_tests.py

# use the following if you want to direct console output to remote server
# cat <(python /opt/monroe/run_tests.py 2>&1) - | nc -q 2 <ServerIP> 8110
# you have to run 'nc -l 8110' at the server side to capture console output
