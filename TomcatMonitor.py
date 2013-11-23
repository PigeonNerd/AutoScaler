#!/usr/bin/python

import urllib2
import json
import time
import socket
import datetime
import glob

""" 
"""
class TomcatMonitor:

    def __init__(self):
        self.vm_name = str(socket.gethostname())
        self.run_int = 2
        self.offset = 0
        self.tomcat_log_pattern = "/var/log/tomcat7/*_access_log.*.txt"
        self.collector_addr = "http://auto-scaler-server:10086"

    def _read_log(self):
        logs = glob.glob(self.tomcat_log_pattern)
        logs.sort();
        #with open(logs[-1], 'r') as f:
        return    

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
    files =  glob.glob("/var/log/tomcat7/*access_log*.txt")
    files.sort()
    offset = 0
    with open(files[-1], 'r') as f:
        f.seek(offset, 0)
        lines = f.readlines()
        offset = f.tell()
        print lines
    time.sleep(7);
    with open(files[-1], 'r') as f:
        f.seek(offset, 0)
        lines = f.readlines()
        print lines
    #try:
    #    cli = TomcatMonitor()
    #    print "Tomcat Monitor is Running ... "
    #    cli.run_forever()
    #except KeyboardInterrupt:
    #    print "Tomcat Monitor is Shutting Down ... "
