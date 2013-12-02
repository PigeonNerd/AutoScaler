#!/bin/bash -x

# Setup proxy so that marmot node can access the external world
export http_proxy=http://ops.marmot.pdl.cmu.local:8888
export https_proxy=http://ops.marmot.pdl.cmu.local:8888

# Setup apt so that it can access the external world
echo Acquire::http::Proxy \"http://ops:8888/\"\; | sudo tee /etc/apt/apt.conf
# Copy over updated version of apt's sources.list
sudo cp -f ../sources.list /etc/apt/sources.list

# Run apt-get update
sudo apt-get update
sudo cp -f ./apt-cache/* /var/cache/apt/archives/

sudo apt-get -y upgrade

sudo apt-get -y install git
sudo apt-get -y install xfsprogs
sudo apt-get -y install cpu-checker
sudo apt-get -y install kvm-ipxe
sudo apt-get -y install pm-utils
sudo apt-get -y install qemu-kvm
sudo apt-get -y install libvirt-bin

# sudo apt-get clean

sudo virsh net-destroy default
sudo virsh net-undefine default

# Create a fake network interface so that Devstack does not take
# over the IP addresss assigned to this marmot node.  The localrc
# file for DevDtack tells DevStack to use this interface
# The first command might fail if tapfoo already exists, so or it with true
sudo ip tuntap add dev tapfoo mode tap
sudo ifconfig tapfoo 172.16.1.254 netmask 255.255.255.0 up

sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

sudo /share/probe/bin/linux-localfs -t xfs -d root /opt 64g
