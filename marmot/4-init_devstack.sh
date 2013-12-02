#!/bin/bash -x

source ./adminrc

nova flavor-create m1.normal 101 1024 0 1
nova flavor-list

nova keypair-add --pub-key ~/.ssh/id_rsa.pub qingzhen
nova keypair-list

nova secgroup-add-rule default tcp 1 65535 0.0.0.0/0
nova secgroup-add-rule default udp 1 65535 0.0.0.0/0 
nova secgroup-add-rule default icmp -1 255 0.0.0.0/0
nova secgroup-list-rules default

echo "copy image to /opt ... "
cp ./cloud-images/ubuntu-12.04-server-cloudimg-amd64-disk1.qcow2 /opt/
echo "converting image to raw format ... "
qemu-img convert -O raw -f qcow2 /opt/ubuntu-12.04-server-cloudimg-amd64-disk1.qcow2 /opt/ubuntu-12.04-server-cloudimg-amd64-disk1.img

glance image-create --name ubuntu-12.04-x86_64-cloud --disk-format raw --container-format ovf --file /opt/ubuntu-12.04-server-cloudimg-amd64-disk1.img
glance image-list
