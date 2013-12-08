#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import json
from AutoScalerCli import Template
from subprocess import call
import urllib2
import threading
from GraphGen import Graph

""" 
    This class implements a CPU Performance Collector.
    The collector works as a base http server (can only serve one request at a time)
    It recieves the periodical updates from performance monitors on each VMs and put 
    them into a Map
""" 

#This is the shared data structure that stores VMs CPU usage
stat_table = []
#Number of stats per VM we need to maintain
statPeriodBound = 2

#Stat file name
stat_file = "collect.log"

#The server address responsible for nova commands
nona_service_address = "http://localhost:10088/"

#Threading timer for heartbeat check
logging_timer = None

#current number of vms
numVMs = 0

#time tick
tick = 0

"""
    we have to maintain one template
"""
template = None

def makeReq(action):
    req = urllib2.Request(nona_service_address + action)
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

def allocate_vm():
    req = makeReq('allocate')
    req.get_method = lambda: 'PUT'
    send(req)

def de_allocate_vm():
    req = makeReq('deallocate')
    req.get_method = lambda: 'DELETE'
    send(req)

def check_high_load(vm):
    for stat in stat_table:
        if stat["res_time"] < template.targetTime:
            return False
    return True

def check_low_load(vm):
    for stat in stat_table:
        if stat["res_time"] > template.targetTime:
            return False
    return True

def logging():
    f = open(stat_file, "a")
    res_time = 0
    for stat in stat_table:
        res_time += stat["res_time"]
    res_time = res_time / 1.0 / numVMs
    stat = {"time": tick,"numVMs" : numVMs, "res_time" : res_time}
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
        global numVMs
        global template
        global logging_timer
        global tick

        # This is to instantiate VMs
        if self.path.endswith('instantiate'):
            print 'instantiate'
            template = Template(jsonMessage['maxVM'], jsonMessage['minVM'], 
                jsonMessage['imagePath'].encode('ascii', 'ignore'), jsonMessage['targetTime'])
            #global template = temp
            template.printTemplate()
            while numVMs < template.minVM:
                numVMs += 1
                allocate_vm()
            logging_timer = threading.Timer(2, logging)
            tick += 2
            logging_timer.start()

           
        elif self.path.endswith('destroy'):
            while numVMs > 0:
                numVMs -= 1
                de_allocate_vm()
            logging_timer.cancel()
        
        else :
            # Convert json Unicode encoding to string
            if jsonMessage["count"] != 0:
                vm = str(jsonMessage["vm"])
                stat = {"res_time": float(jsonMessage["res_time"])}; 
                self.insert(stat)

                if  numVMs <  template.maxVM and check_high_load:
                    numVMs += 1
                    allocate_vm()
                    print "High load detect ! spawn new VM"
                elif  numVMs >  template.minVM and check_low_load:
                    numVMs -= 1
                    de_allocate_vm()
                    print "Low load detect ! de-alloc one VM"

    #insert into the stat table
    def _insert(self, stat):
        stat_table.insert(0, stat)

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
