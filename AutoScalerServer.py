#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import json
from AutoScalerCli import Template
from subprocess import call
import urllib2
import threading
#from GraphGen import Graph

""" 
    This class implements a CPU Performance Collector.
    The collector works as a base http server (can only serve one request at a time)
    It recieves the periodical updates from performance monitors on each VMs and put 
    them into a Map
""" 

#This is the shared data structure that stores VMs CPU usage
stat_table = []
#Number of stats per VM we need to maintain
statPeriodBound = 3

#Stat file name
stat_file = "collect.log"

#The server address responsible for nova commands
nona_service_address = "http://localhost:10085/"

#Threading timer for heartbeat check
logging_timer = None

#current number of vms
numVMs = 0

#time tick
tick = 0

#High load, low load range
highRange = 1.2

#is instantiate
initialized = False

# is some vm dead
isDead = 0

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

def check_high_load():
    if len(stat_table) < statPeriodBound:
        return False

    for stat in stat_table:
        if stat["res_time"] < template.targetTime * highRange:
            return False
    return True

def check_low_load():
    if len(stat_table) < statPeriodBound:
        return False

    for stat in stat_table:
        if stat["res_time"] > 1.8:
            return False
    return True

def logging():
    global tick
    global logging_timer
    global isDead
    print "start to log !"
    f = open(stat_file, "a")
    res_time = 0
    for stat in stat_table:
        res_time += stat["res_time"]
    res_time = res_time / 1.0 / statPeriodBound
    stat = {"time": tick,"numVMs" : numVMs - isDead, "res_time" : res_time}
    json.dump(stat, f)
    f.write("\n")
    f.close
    tick += 5
    logging_timer = threading.Timer(5, logging)
    logging_timer.start()

#Create custom HTTPRequestHandler class
class TomcatStatusHandler(BaseHTTPRequestHandler):

    def do_PUT(self):
        print "LOCKED, a VM get killed"
        self.send_response(201)
        self.end_headers()
        global isDead
        isDead += 1
    def do_DELETE(self):
        print "UNLOCKED, a VM get recovered"
        self.send_response(201)
        self.end_headers()
        global isDead
        isDead -= 1 
        
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
        global initialized
        global isDead

        # This is to instantiate VMs
        if self.path.endswith('instantiate'):
            print 'instantiate'
            template = Template(jsonMessage['maxVM'], jsonMessage['minVM'], 
                jsonMessage['imagePath'].encode('ascii', 'ignore'), jsonMessage['targetTime'])
            #global template = temp
            logging()
            template.printTemplate()
            initialized = True
            while numVMs < template.minVM:
                numVMs += 1
                allocate_vm()
           
        elif self.path.endswith('destroy'):
            #finished = True
            initialized = False
            logging_timer.cancel()
            while numVMs > 0:
                numVMs -= 1
                de_allocate_vm()
        else :
            if initialized:
                # Convert json Unicode encoding to string
                if jsonMessage["count"] == 0 and numVMs > template.minVM:
                    while numVMs > template.minVM:
                        numVMs -= 1;
                        de_allocate_vm()

                if jsonMessage["count"] != 0:
                    stat = {"res_time": float(jsonMessage["res_time"])};
                    print "Receive %f, Target %f (high: %f, low: %f)" % (stat["res_time"], 
                        template.targetTime, template.targetTime * highRange, 2.0)
                    print stat_table
                    self._insert(stat)

                    if  numVMs <  template.maxVM and check_high_load() and isDead < 1:
                        numVMs += 1
                        allocate_vm()
                        print "High load detect ! spawn new VM"

                    elif numVMs == template.maxVM and check_high_load() and isDead < 1:
                        print "High load detect, but already reach max VMs"
                    elif  numVMs >  template.minVM and check_low_load() and isDead < 1:
                        numVMs -= 1
                        de_allocate_vm()
                        print "Low load detect ! de-alloc one VM"
                    elif numVMs == template.minVM and check_low_load() and isDead < 1:
                        print "Low load detect, but already reach min VMs"

    #insert into the stat table
    def _insert(self, stat):
        if len(stat_table) < statPeriodBound:
            stat_table.insert(0, stat)
        else:
            stat_table.insert(0, stat)
            stat_table.pop()

def run():
    #print('http server is starting...')
    #ip and port of servr
    #by default http server port is 10088
    server_address = ('0.0.0.0', 10088)
    #handle = CPUStatusHandler()
    httpd = HTTPServer(server_address, TomcatStatusHandler)
    #print('http server is running...')
    httpd.serve_forever()
    
if __name__ == '__main__':
    run()
    
