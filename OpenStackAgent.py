#!/usr/bin/python

import BaseHTTPServer
from novaclient.v1_1 import client

# vm pool
pool_size = 2
lazy_start = True

# vm metadata
image_id = 'to-be-decided'
flavor_id = 'to-be-decided'
ssh_keyname = 'to-be-decided'

# openstack login credentials
username = 'qzheng7'
password = 'qzheng7'
tenant_name = 'qzheng7'
service_url = 'http://qzheng7os1:5000/v2.0/'

# python nova client
cli = client.Client(username, password, tenant_name, service_url, service_type="compute")

# # # # # # # # # # #
# Openstack Helpers #

def _open_stack_get_ip_(srv):
    """ retrieve server ip; return the last ip if we get multiple ips """
    addr_info = srv.addresses
    for net in addr_info.keys():
        for addr in addr_info[net]:
             ip = addr['addr']
    return ip


def _open_stack_start_vm_(srv, srv_name):
    """ start a specified vm and rename it to a new name """
    if srv is not None:
        if srv.name != srv_name:
            srv.update(name=srv_name)
        if srv.status == 'SHUTOFF':
            srv.start()


def _open_stack_stop_vm_(srv, srv_name):
    """ stop a specific vm and rename it to a new name """
    if srv is not None:
        if srv.status != 'SHUTOFF':
            srv.stop()
        if srv.name != srv_name:
            srv.update(name=srv_name)


def _open_stack_create_vm_(srv_name):
    """ create a new vm if it has not yet been created """
    for srv in cli.servers.list():
        if srv.name == srv_name:
            if not lazy_start and srv.status == 'SHUTOFF':
                srv.start()
            return srv
    return cli.servers.create(srv_name, image_id, flavor_id, key_name=ssh_keyname)

# # # # # # # # # # #
# VM Pool Interface #

def _vm_pool_init_():
    for srv_num in range(1, pool_size + 1):
        srv_name = 'pool-vm-' + str(srv_num)
        srv = _open_stack_create_vm_(srv_name)
        cli.servers.set_meta(srv, {'pool-id': srv_name, 'pool-status': 'idle', 'pool-priority': '1'})
    print 'vm pool initialized'


def _vm_pool_pop_(srv_name):
    for srv in cli.servers.list():
        if srv.metadata['pool-status'] == 'idle':
            _open_stack_start_vm_(srv, srv_name)
            cli.servers.set_meta(srv, {'pool-status': 'active'})
            return srv
    return None


def _vm_pool_push_(srv_name):
    for srv in cli.servers.list():
        if srv.name == srv_name:
            _open_stack_stop_vm_(srv, srv.metadata['pool-id'])
            cli.servers.set_meta(srv, {'pool-status': 'idle'})
            return srv
    return None

def _vm_pool_list_():
    srvs = []
    for srv in cli.servers.list():
        if srv.metadata['pool-id'] is not None:
            srvs.append({'name': str(srv.name), 'status': str(srv.status),
                         'pool-id': str(srv.metadata['pool-id']), 'pool-status': str(srv.metadata['pool-status']),
                         'pool-priority': int(srv.metadata['pool-priority']), 'ip': str(_open_stack_get_ip_(srv))})
    print srvs


class OpenStackAgent(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        _vm_pool_list_()
        self.send_response(200)
        self.end_headers()

    def do_PUT(self):
        _vm_pool_init_()
        self.send_response(201)
        self.end_headers()


if __name__ == '__main__':
    try:
        server = BaseHTTPServer.HTTPServer(('0.0.0.0', 10087), OpenStackAgent)
        print 'Open Stack Agent is Running ... '
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Open Stack Agent is Shutting Down ... '
        server.shutdown()