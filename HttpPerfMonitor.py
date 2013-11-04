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
class PerfMonitor:

    def __init__(self):
        self.vm_name = str(socket.gethostname())
        self.run_int = 2
        self.stat_path = "/proc/stat"
        self.collector_addr = "http://vm-collector-host:8081"
        self.cpu_stat = {"user": 0, "nice": 0, "system": 0, "idle": 0, "iowait": 0}

    @staticmethod
    def _parse_stat(raw_data):
        cpu_times = raw_data.split()[1:6]
        return {"user": int(cpu_times[0]), "nice": int(cpu_times[1]),
                "system": int(cpu_times[2]), "idle": int(cpu_times[3]), "iowait": int(cpu_times[4])}

    @staticmethod
    def _get_tiemstamp():
        ts = time.time()
        return datetime.datetime.fromtimestamp(ts).strtime('%H:%M:%S %Y-%m-%d')

    def _get_cpu_stat(self):
        with open(self.stat_path, 'r') as f:
            file_line = f.readline().rstrip()
            return file_line

    def _cal_cpu_usage(self, new_cpu_stat):
        user_time = new_cpu_stat["user"] - self.cpu_stat["user"]
        nice_time = new_cpu_stat["nice"] - self.cpu_stat["nice"]
        system_time = new_cpu_stat["system"] - self.cpu_stat["system"]
        idle_time = new_cpu_stat["idle"] - self.cpu_stat["idle"]
        iowait_time = new_cpu_stat["iowait"] - self.cpu_stat["iowait"]
        total_time = user_time + nice_time + system_time + idle_time + iowait_time
        return {"user": user_time * 100 / total_time, "nice": nice_time * 100 / total_time,
                "system": system_time * 100 / total_time, "idle": idle_time * 100 / total_time,
                "iowait": iowait_time * 100 / total_time, "_ts": self._get_timestamp()}

    def _update_stat(self, new_cpu_stat):
        self.cpu_stat["user"] = new_cpu_stat["user"]
        self.cpu_stat["nice"] = new_cpu_stat["nice"]
        self.cpu_stat["system"] = new_cpu_stat["system"]
        self.cpu_stat["idle"] = new_cpu_stat["idle"]
        self.cpu_stat["iowait"] = new_cpu_stat["iowait"]

    def _mk_req(self, data):
        req = urllib2.Request(self.collector_addr)
        req.add_header('Content-Type', 'application/json')
        req.add_header('User-Agent', 'perf-monitor/0.0.1')
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
        raw_data = self._get_cpu_stat()
        new_cpu_stat = self._parse_stat(raw_data)
        usage_data = self._cal_cpu_usage(new_cpu_stat)
        self._update_stat(new_cpu_stat)
        #usage_data = {"user": 1, "nice": 2, "system": 3, "idle": 4, "iowait": 5}
        self._send_req(json.dumps({"vm": self.vm_name, "cpu_stat": usage_data}))

    def run_forever(self):
        while True:
            self.run_once()
            time.sleep(self.run_int)

if __name__ == '__main__':
    try:
        cli = PerfMonitor()
        print "Perf Monitor is Running ... "
        cli.run_forever()
    except KeyboardInterrupt:
        print "Perf Monitor is Shutting Down ... "
