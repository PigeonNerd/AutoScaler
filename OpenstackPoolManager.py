#!/usr/bin/python

import os
import json
import time
import urllib2
import BaseHTTPServer
from novaclient.v1_1 import client


class PoolManager:

    def __init__(self):
        # vm pool config
        self.pool_id = str(time.time())
        self.bulk_size = 3
        self.usage_index = 0
        self.pool_indices = []
        self.lazy_start = False
        self.lb_reload_script = './haproxy/haproxy-reload.sh'
        self.lb_servers_list = './haproxy/haproxy-servers.cfg'

        # vm boot metadata
        self.flavor_id = '101'
        self.ssh_keyname = 'qingzhen'
        self.image_id = '7e7ec42f-facb-4358-8af0-1751a863d496'

        # openstack admin credentials
        self.username = 'admin'
        self.password = '123456'
        self.tenant_name = 'admin'
        self.service_url = 'http://openstack-host:5000/v2.0/'

        # vm heartbeats
        self.heartbeats = {}
        self.autoscaler_addr = 'http://load-balancer:10088'

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

    def _open_stack_create_vm_(self, srv_name, metadata):
        srv = self.cli.servers.create(srv_name, self.image_id, self.flavor_id, key_name=self.ssh_keyname)
        while srv.status != 'ACTIVE':
            time.sleep(5)
            srv = self.cli.servers.get(srv.id)
        self.cli.servers.set_meta(srv, metadata)
        return srv

    def _open_stack_try_create_vm_(self, srv_name, metadata={}):
        """ create a new vm if it has not yet been created """
        for srv in self.cli.servers.list():
            if srv.name == srv_name:
                if not self.lazy_start and srv.status == 'SHUTOFF':
                    srv.start()
                self.cli.servers.set_meta(srv, metadata)
                return srv
        return self._open_stack_create_vm_(srv_name, metadata)

    def _open_stack_start_vm_(self, srv, srv_name):
        """ start a specified vm and rename it to a new name """
        if srv is None:
            if srv_name is None:
                return None
            srv = self._open_stack_try_create_vm_(srv_name)
        if srv_name is not None and srv_name != srv.name:
            srv.update(name=srv_name)
        if srv.status == 'SHUTOFF':
            srv.start()
        return srv

    def _lb_update_backend_srvs_(self):
        with open(self.lb_servers_list, 'w') as f:
            for srv in self.cli.servers.list():
                ip = str(self._open_stack_get_ip_(srv))
                if self._is_pool_member(srv) and srv.metadata['pool-state'] == 'active':
                    f.write('        ' + 'server' + ' ' + str(srv.metadata['pool-usage']) + ' ' +
                            ip + ':8080' + ' ' + 'check inter 50000\n')
            f.flush()
        os.system(self.lb_reload_script)

    def _is_pool_member(self, srv):
        if 'pool-id' in srv.metadata:
            if srv.metadata['pool-id'] == self.pool_id:
                return True
        return False

    def _vm_pool_bulk_(self, bulk_size=0):
        if bulk_size == 0:
            bulk_size = self.bulk_size
        for _ in range(1, bulk_size + 1):
            idx = 1
            while idx in self.pool_indices:
                idx += 1
            srv_name = 'pool-vm-' + str(idx)
            self.pool_indices.append(idx)
            self._open_stack_try_create_vm_(srv_name,
                                            {'pool-id': str(self.pool_id), 'pool-state': 'idle', 'pool-usage': 'none'})

    def _vm_pool_pop_(self, old_ip=None):
        for srv in self.cli.servers.list():
            if self._is_pool_member(srv) and srv.metadata['pool-state'] == 'idle':
                self.usage_index += 1
                usage_name = 'web-server-' + str(self.usage_index)
                self._open_stack_start_vm_(srv, None)
                self.cli.servers.set_meta(srv, {'pool-state': 'active', 'pool-usage': usage_name})
                ip = str(self._open_stack_get_ip_(srv))
                self.heartbeats[ip] = (float(-500), old_ip)
                print 'POP: ' + ip + ' - ' + str(self.heartbeats[ip])
                return srv
        self._vm_pool_bulk_(bulk_size=1)
        return self._vm_pool_pop_(old_ip=old_ip)

    def _vm_pool_push_(self):
        for srv in self.cli.servers.list():
            if self._is_pool_member(srv) and srv.metadata['pool-state'] == 'active':
                self.cli.servers.set_meta(srv, {'pool-state': 'idle', 'pool-usage': 'none'})
                ip = str(self._open_stack_get_ip_(srv))
                del self.heartbeats[ip]
                print 'PUSH: ' + ip
                return srv
        return None  # nothing to push from pool

    def _vm_pool_list_(self):
        srv_list = []
        for srv in self.cli.servers.list():
            if self._is_pool_member(srv):
                srv_list.append({'name': str(srv.name), 'status': str(srv.status),
                                 'pool-state': str(srv.metadata['pool-state']), 'pool-usage': str(srv.metadata['pool-usage']),
                                 'ip': str(self._open_stack_get_ip_(srv))})
        return srv_list

    def _vm_pool_hb_(self, ip):
        if ip in self.heartbeats:
            (_dummy, old_ip) = self.heartbeats[ip]
            self.heartbeats[ip] = (float(time.time()), old_ip)
            print 'HB: ' + ip + ' - ' + str(self.heartbeats[ip])

    def _vm_pool_check(self):
        now = float(time.time())
        to_be_removed = []
        newly_recovered = []
        for ip in self.heartbeats:
            (hb, old_ip) = self.heartbeats[ip]
            if hb < 0:
                self.heartbeats[ip] = (hb + 5, old_ip)
            else:
                if hb + 15 < now:
                    to_be_removed.append(ip)
                else:
                    if old_ip is not None:
                        newly_recovered.append(ip)
                        self.heartbeats[ip] = (hb, None)
                        self._unlock_()
        for ip in to_be_removed:
            del self.heartbeats[ip]
            for srv in self.cli.servers.list():
                if self._is_pool_member(srv) and str(self._open_stack_get_ip_(srv)) == ip:
                    self.cli.servers.delete(srv)
            self._vm_pool_pop_(old_ip=ip)
            self._lock_()
        print 'CHK: ' + str(self.heartbeats)
        return to_be_removed, newly_recovered

    def _lock_(self):
        req = urllib2.Request(self.autoscaler_addr)
        req.get_method = lambda: 'PUT'
        try:
            urllib2.urlopen(req)
        except urllib2.URLError as ue:
            print ue.reason
        except urllib2.HTTPError as he:
            print "%s - %s" % (he.code, he.reason)

    def _unlock_(self):
        req = urllib2.Request(self.autoscaler_addr)
        req.get_method = lambda: 'DELETE'
        try:
            urllib2.urlopen(req)
        except urllib2.URLError as ue:
            print ue.reason
        except urllib2.HTTPError as he:
            print "%s - %s" % (he.code, he.reason)

manager = PoolManager()

class OpenstackAgent(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        srv_list = manager._vm_pool_list_()
        print 'SRV-LIST:\n'
        for srv in srv_list:
            if srv['pool-state'] == 'active':
                print srv['pool-usage'] + ' - ' + srv['status'] + '\n'
        print 'END LIST\n'

    def do_POST(self):
        self.send_response(201)
        self.end_headers()
        content_len = self.headers.getheader('Content-Length')
        post_body = self.rfile.read(int(content_len))
        ip = str(json.loads(post_body)['vm'])
        manager._vm_pool_hb_(ip)

    def do_PUT(self):
        self.send_response(204)
        self.end_headers()
        srv = manager._vm_pool_pop_()
        manager._lb_update_backend_srvs_()
        print 'ADD: ' + srv.name + '\n'

    def do_DELETE(self):
        self.send_response(204)
        self.end_headers()
        srv = manager._vm_pool_push_()
        manager._lb_update_backend_srvs_()
        print 'DEL: ' + srv.name + '\n'

    def do_HEAD(self):
        self.send_response(204)
        self.end_headers()
        (failed, recovered) = manager._vm_pool_check()
        if len(failed) > 0:
            manager._lb_update_backend_srvs_()
        print 'FAILED: ' + str(failed) + '\n'
        print 'RECOVERED: ' + str(recovered) + '\n'

if __name__ == '__main__':
    try:
        manager._vm_pool_bulk_(bulk_size=2)
        print 'Initializing Openstack Pool Manager ... '
        server = BaseHTTPServer.HTTPServer(('0.0.0.0', 10086), OpenstackAgent)
        print 'Openstack Pool Manager is Running ... '
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Openstack Pool Manager is Shutting Down ... '
        server.shutdown()
