#!/bin/bash

rm -f collect.log
sudo rm -f /var/siege.log

python AutoScalerCli.py instantiate /proj/OpenStackSys/proj2/scripts/autoscaler_templates/tomcat.template_1
sleep 5
sudo /proj/OpenStackSys/group_data/test/load_test_3 http://localhost:8088/webserver/
python AutoScalerCli.py destroy /proj/OpenStackSys/proj2/scripts/autoscaler_templates/tomcat.template_1
