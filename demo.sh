#!/bin/bash

rm -f /tmp/*.err
rm -f /tmp/*.log

python /opt/AutoScaler/OpenstackPoolManager.py 1>/tmp/Manager.log 2>/tmp/Manager.err &
python /opt/AutoScaler/OpenstackPoolAuditor.py 1>/tmp/Auditor.log 2>/tmp/Auditor.err &
python /opt/AutoScaler/HAProxyMonitor.py 1>/tmp/Monitor.log 2>/tmp/Monitor.err &
python /opt/AutoScaler/AutoScalerServer.py 1>/tmp/Server.log 2>/tmp/Server.err &
