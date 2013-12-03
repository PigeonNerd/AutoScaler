#!/usr/bin/python

import BaseHTTPServer
from novaclient.v1_1 import client

cli = client.Client('qzheng7', 'qzheng7', 'qzheng7', 'http://qzheng7os1:5000/v2.0/', service_type="compute")


def _open_stack_start_vm_(srv, srv_name):
    if srv is not None:
        if srv.name != srv_name:
            srv.update(name=srv_name)
        if srv.status == 'SHUTOFF':
            srv.start()


def _open_stack_stop_vm_(srv, srv_name):
    if srv is not None:
        if srv.status != 'SHUTOFF':
            srv.stop()
        if srv.name != srv_name:
            srv.update(name=srv_name)


def _open_stack_create_vm_(srv_name):
    for srv in cli.servers.list():
        if srv.name == srv_name:
            return srv
#        if srv.status == 'SHUTOFF':
#           srv.start()
    return cli.servers.create(srv_name, 'image-id', 'flavor-id')


def _vm_pool_init_():
    for srv_name in ['vm1', 'vm2', 'vm3']:
        srv = _open_stack_create_vm_(srv_name)
        cli.servers.set_meta(srv, {'pool-id': srv_name, 'pool-status': 'idle'})
    return


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


class OpenStackAgent(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        _vm_pool_init_()


if __name__ == '__main__':
    try:
        server = BaseHTTPServer.HTTPServer(('0.0.0.0', 10087), OpenStackAgent)
        print 'Open Stack Agent is Running ... '
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Open Stack Agent is Shutting Down ... '
        server.shutdown()