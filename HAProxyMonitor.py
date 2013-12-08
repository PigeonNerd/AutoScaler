#!/usr/bin/python

import urllib2
import json
import time
import glob


class TomcatJkMonitor:

    def __init__(self):
        self.log_offset = 0
        self.srv_address = "http://load-balancer:10088"
        self.check_interval = 5
        self.logfile_path = "/var/log/haproxy.log"

    @staticmethod
    def _parse_log(lines):
        total = 0
        count = 0
        for line in lines:
            if line.fine('GET') >= 0:
                if line.find('<NOSRV>') < 0:
                    res_time = line.split(':')[1].split(' ')[4].split('/')[3]
                    count += 1
                    total += float(res_time) / 1000
        return (total / count) if count != 0 else 0, count

    def _read_and_parse_log(self):
        logs = glob.glob(self.logfile_path)
        logs.sort()
        if logs.__len__() > 0:
            with open(logs[-1], 'r') as f:
                f.seek(0, 2) # jump to the end of the file
                size = f.tell()
                if size < self.log_offset:  # this is a new log file
                    self.log_offset = 0  # reset the file offset
                f.seek(self.log_offset, 0)  # continue from the last checkpoint
                lines = f.readlines()
                self.log_offset = f.tell()  # save the current checkpoint
            (avg_res, count) = self._parse_log(lines)
            return {"res_time": avg_res, "count": count}
        return {"count": 0}  # no log files detected

    def _mk_req(self, data):
        req = urllib2.Request(self.srv_address)
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'tomcat-jk-monitor/0.0.1')
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
        data = self._read_and_parse_log()
        self._send_req(json.dumps(data))

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(self.check_interval)

if __name__ == '__main__':
    try:
        cli = TomcatJkMonitor()
        print "Tomcat Jk Monitor is Running ... "
        cli.run_forever()
    except KeyboardInterrupt:
        print "Tomcat Jk Monitor is Shutting Down ... "
