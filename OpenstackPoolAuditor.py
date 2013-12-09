#!/usr/bin/python

import urllib2
import time


class OpenstackPoolAuditor:

    def __init__(self):
        self.check_interval = 5
        self.srv_address = "http://load-balancer:10086"

    def _mk_req(self):
        req = urllib2.Request(self.srv_address)
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'openstack-auditor/0.0.1')
        req.get_method = lambda: 'HEAD'
        return req

    def _send_req(self):
        try:
            urllib2.urlopen(self._mk_req())
        except urllib2.URLError as ue:
            print ue.reason
        except urllib2.HTTPError as he:
            print "%s - %s" % (he.code, he.reason)

    def run_once(self):
        self._send_req()

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(self.check_interval)

if __name__ == '__main__':
    try:
        cli = OpenstackPoolAuditor()
        print "Openstack Pool Auditor is Running ... "
        cli.run_forever()
    except KeyboardInterrupt:
        print "Openstack Pool Auditor is Shutting Down ... "
