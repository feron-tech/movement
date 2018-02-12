#!/bin/bash
# iperf3 in four parallel ports (Daemon mode), see 'pstree'
# RUN: './multi_iperf3.sh'
# to stop all 'pkill iperf3;' 
iperf3 -s -p 5201 -D; iperf3 -s -p 5202 -D; iperf3 -s -p 5203 -D; iperf3 -s -p 5204 -D; 
