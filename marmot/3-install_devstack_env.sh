#!/bin/bash -x

# Setup proxy so that marmot node can access the external world
export http_proxy=http://ops.marmot.pdl.cmu.local:8888
export https_proxy=http://ops.marmot.pdl.cmu.local:8888

sudo rm -rf ./devstack

git clone https://github.com/openstack-dev/devstack.git

cp ./localrc ./devstack/

cd devstack

./stack.sh
