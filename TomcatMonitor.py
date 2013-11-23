#!/usr/bin/python

import urllib2
import json
import time
import socket
import datetime

""" 
  This class implements a Performance Monitor running on a
  virtual machine and periodically sending status report to
  a paired Performance Collector listening on a physical host.
  Existing implementation ONLY takes CPU usage into consideration
  and is designed to running on UBUNTU clients ONLY.
"""
class TomcatMonitor:

    def __init__(self):
        self.vm_name = str(socket.gethostname())
        self.run_int = 2
        self.collector_addr = "http://auto-scaler-server:10086"

    def _mk_req(self, data):
        req = urllib2.Request(self.collector_addr)
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'tomcat-monitor/0.0.1')
        req.add_data(data)
        return req

    def _send_req(self, data):
        try:
            urllib2.urlopen(self._mk_req(data))
        except urllib2.URLError as ue:
            print ue.reason
        except urllib2.HTTPError as he:
            print "%s - %s" % (he.code, he.reason)

    def run_once(self):
        self._send_req(json.dumps({"vm": self.vm_name, "res_time": 10}))

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(self.run_int)

if __name__ == '__main__':
    try:
        cli = TomcatMonitor()
        print "Tomcat Monitor is Running ... "
        cli.run_forever()
    except KeyboardInterrupt:
        print "Tomcat Monitor is Shutting Down ... "
