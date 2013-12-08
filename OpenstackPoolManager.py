#!/usr/bin/python

import json
import BaseHTTPServer
from novaclient.v1_1 import client


class PoolManager:

    def __init__(self):
        # vm pool config
        self.bulk_size = 3
        self.usage_index = 0
        self.pool_indices = []
        self.lazy_start = False

        # vm boot metadata
        self.flavor_id = '101'
        self.ssh_keyname = 'qingzhen'
        self.image_id = 'to-be-decided'

        # openstack admin credentials
        self.username = 'admin'
        self.password = '123456'
        self.tenant_name = 'admin'
        self.service_url = 'http://openstack-host:5000/v2.0/'

        # python nova client
        self.cli = client.Client(self.username, self.password,
                                 self.tenant_name, self.service_url, service_type="compute")

    @staticmethod
    def _open_stack_get_ip_(srv):
        """ retrieve server ip; return the last ip if we get multiple ips """
        addr_info = srv.addresses
        for net in addr_info.keys():
            for addr in addr_info[net]:
                 ip = addr['addr']
        return ip


    def _open_stack_create_vm_(self, srv_name):
        """ create a new vm if it has not yet been created """
        for srv in self.cli.servers.list():
            if srv.name == srv_name:
                if not self.lazy_start and srv.status == 'SHUTOFF':
                    srv.start()
                return srv
        return self.cli.servers.create(srv_name,
                                       self.image_id, self.flavor_id, key_name=self.ssh_keyname)


    def _open_stack_start_vm_(self, srv, srv_name):
        """ start a specified vm and rename it to a new name """
        if srv is None:
            srv = self._open_stack_create_vm_(srv_name)
        if srv_name is not None and srv_name != srv.name:
            srv.update(name=srv_name)
        if srv.status == 'SHUTOFF':
            srv.start()
        return srv

    def _vm_pool_bulk_(self):
        for _dummy in range(1, self.bulk_size + 1):
            idx = 1
            while idx in self.pool_indices:
                idx += 1
            srv_name = 'pool-vm-' + str(idx)
            self.pool_indices.append(idx)
            srv = self._open_stack_create_vm_(srv_name)
            self.cli.servers.set_meta(srv, {'pool-state': 'idle', 'pool-usage': 'none'})

    def _vm_pool_pop_(self):
        for srv in self.cli.servers.list():
            if srv.metadata['pool-state'] == 'idle':
                self.usage_index += 1
                usage_name = 'web-server-' + str(self.usage_index)
                self._open_stack_start_vm_(srv, None)
                self.cli.servers.set_meta(srv, {'pool-state': 'active', 'pool-usage': usage_name})
                return srv
        self._vm_pool_bulk_()
        return self._vm_pool_pop_()

    def _vm_pool_push_(self):
        for srv in self.cli.servers.list():
            if srv.metadata['pool-state'] == 'active':
                self.cli.servers.set_meta(srv, {'pool-state': 'idle', 'pool-usage': 'none'})
                return srv
        return None

    def _vm_pool_list_(self):
        srv_list = []
        for srv in self.cli.servers.list():
            if srv.metadata['pool-state'] is not None:
                srv_list.append({'name': str(srv.name), 'status': str(srv.status),
                                 'pool-state': str(srv.metadata['pool-state']), 'pool-usage': str(srv.metadata['pool-usage']),
                                 'ip': str(self._open_stack_get_ip_(srv))})
        return srv_list


manager = PoolManager()

class OpenstackAgent(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        srv_list = manager._vm_pool_list_()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps(srv_list))
        self.wfile.close()

    def do_POST(self):
        manager._vm_pool_bulk_()
        srv_list = manager._vm_pool_list_()
        self.send_response(204)
        self.end_headers()

    def do_PUT(self):
        srv = manager._vm_pool_pop_()
        self.send_response(201)
        self.end_headers()
        self.wfile.write(json.dumps({'name': srv.name}))
        self.wfile.close()

    def do_DELETE(self):
        srv = manager._vm_pool_push_()
        self.send_response(202)
        self.end_headers()
        self.wfile.write(json.dumps({'name': srv.name}))
        self.wfile.close()

if __name__ == '__main__':
    try:
        server = BaseHTTPServer.HTTPServer(('0.0.0.0', 10085), OpenstackAgent)
        print 'Openstack Agent is Running ... '
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Openstack Agent is Shutting Down ... '
        server.shutdown()