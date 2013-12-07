#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import json
from AutoScalerCli import Template
from subprocess import call
import urllib2
import threading

""" 
    This class implements a CPU Performance Collector.
    The collector works as a base http server (can only serve one request at a time)
    It recieves the periodical updates from performance monitors on each VMs and put 
    them into a Map
""" 

#This is the shared data structure that stores VMs CPU usage
stat_table = dict()
#Number of stats per VM we need to maintain
statPeriodBound = 2

#Stat file name
stat_file = "collect.log"

#The server address responsible for nova commands
nona_service_address = "http://localhost:10087/"

#Threading timer for heartbeat check
logging_timer = None

"""
    we have to maintain one template
"""
template = ''

def makeReq(action):
    req = urllib2.Request(collector_addr + action)
    req.add_header('Content-Type', 'application/json')
    req.add_header('User-Agent', 'tomcat-monitor/0.0.1')
    return req

def send(req):
    try:
        urllib2.urlopen(req)
    except urllib2.URLError as ue:
        print ue.reason
    except urllib2.HTTPError as he:
        print "%s - %s" % (he.code, he.reason)

def allocate_vm(vmIDs):
   data = json.dumps({"ids" : vmIDs})
   req = makeReq('allocate')
   req.add_data(data)
   send(req)

def de_allocate_vm(vmIDs):
    data = json.dumps({"ids" : vmID})
    req = makeReq('deallocate')
    req.add_data(data)
    send(req)

def check_high_load(vm):
    if stat_table[vm]["num"] == statPeriodBound:
        stats = stat_table[vm]["num"]["stats"]
        for stat in stats:
            if stat["res_time"] < template.targetTime:
                return False
        # here means we have high load lasts for 5 seconds
        return True
    return False

def check_low_load(vm):
    if stat_table[vm]["num"] == statPeriodBound:
        stats = stat_table[vm]["num"]["stats"]
        for stat in stats:
            if stat["res_time"] >= template.targetTime:
                return False
        # here means we have low load lasts for 5 seconds
        return True
    return False

def logging():
    f = open(stat_file, "a")
    res_time = 0;
    for vm in stat_table:
        tmp = 0;
        for stat in vm["stats"]:
            tmp += stat["res_time"]
        res_time += tmp / 1.0 / len(vm["stats"])

    res_time = restime / 1.0 / len(stat_table)
    stat = {"numVMs": len(stat_table), "res_time": res_time}
    json.dump(stat, f)
    f.write("\n")
    f.close

#Create custom HTTPRequestHandler class
class TomcatStatusHandler(BaseHTTPRequestHandler):

    #handle POST command
    def do_POST(self):
        self.send_response(201)
        self.end_headers()
        content_type = self.headers.getheader('Content-Type')
        content_len = self.headers.getheader('Content-Length')
        post_body = self.rfile.read(int(content_len))
        jsonMessage = json.loads(post_body)

        # This is to instantiate VMs
        if self.path.endswith('instantiate'):
            print 'instantiate'
            template = Template(jsonMessage['maxVM'], jsonMessage['minVM'], 
                jsonMessage['imagePath'].encode('ascii', 'ignore'), jsonMessage['targetTime'])
            template.printTemplate()

            IDs = []
            for i in range(1,template.minVM + 1):
                IDs.insert(0, "vm" + i)
            allocate_vm(IDs)
            logging_timer = threading.Timer(3.0, logging)
            logging_timer.start()
           
        elif self.path.endswith('destroy'):
            heartbeat_timer.cancel()
            IDs = stat_table.keys()
            de_allocate_vm(IDs)
            logging_timer.cancel()
        
        else :
            # Convert json Unicode encoding to string
            if jsonMessage["count"] != 0:
                vm = str(jsonMessage["vm"])
                stat = {"res_time": int(jsonMessage["res_time"])}; 
                self._insert(vm, stat)
                #self._printToFile(vm)
                if len(stat_table) < template.maxVM and check_high_load(vm):
                    id = "vm" + len(stat_table) + 1
                    allocate_vm([""])

    #insert into the stat table
    def _insert(self, vm, stat):
        #print stat_table
        if vm in stat_table:
            if stat_table[vm]["num"] < statPeriodBound:
                stat_table[vm]["stats"].insert(0, stat)
                stat_table[vm]["num"] += 1
            else:
                stat_table[vm]["stats"].pop()
                stat_table[vm]["stats"].insert(0, stat)
        else:
            stat_table[vm] = dict()
            stat_table[vm]["num"] = 1
            stat_table[vm]["stats"] = [stat]

    #dump the stat table into a file
    def _printToFile(self, vm):
        f = open(stat_file, "a")
        f.write(vm + ": ")
        json.dump(stat_table[vm]["stats"][0], f)
        f.write("\n")
        f.close

def run():
    #print('http server is starting...')
    #ip and port of servr
    #by default http server port is 10086
    server_address = ('0.0.0.0', 10086)
    #handle = CPUStatusHandler()
    httpd = HTTPServer(server_address, TomcatStatusHandler)
    #print('http server is running...')
    httpd.serve_forever()
    
if __name__ == '__main__':
    run()
