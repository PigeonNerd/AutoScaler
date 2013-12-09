#!/bin/bash

cat ./haproxy/haproxy.cfg ./haproxy/haproxy-servers.cfg | sudo tee /etc/haproxy/haproxy.cfg > /dev/null
sudo service haproxy reload
