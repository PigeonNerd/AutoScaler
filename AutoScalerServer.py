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
statPeriodBound = 5
# heartbeat periodic
HEART_BEAT_BOUND = 10
# pull in progress periodic
INPROGRESS_BOUND = 5

#Stat file name
stat_file = "collect.log"

#The server address responsible for nova commands
nona_service_address = "http://localhost:10087/"

# This is a big flag that sets if we already tried to spawn new VMs
inProgress = False
inProgress_timer = None

#Threading timer for heartbeat check
heartbeat_timer = None

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

def allocate_vm(num):
   data = json.dumps({"num" : num})
   req = makeReq('allocate')
   req.add_data(data)
   send(req)

def de_allocate_vm(vmID):
    data = json.dumps({"id" : vmID})
    req = makeReq('deallocate')
    req.add_data(data)
    send(req)

def heartbeat():
    req = makeReq('heartbeat')
    response = urllib2.urlopen(req)
    # TODO: need to check if any vm killed

def check_high_load(vm):
    if not inProgress and stat_table[vm]["num"] == statPeriodBound:
        stats = stat_table[vm]["num"]["stats"]
        for stat in stats:
            if stat["res_time"] < template.targetTime:
                return
        # here means we have high load lasts for 5 seconds
        return True
    return False

def pull_inProgress():
    req = makeReq("isOnline")
    send(req)

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
            allocate_vm(template.minVM)
            inProgress = True
            inProgress_timer = threading.timer(INPROGRESS_BOUND, pull_inProgress)
            inProgress_timer.start()
            heartbeat_timer = threading.Timer(HEART_BEAT_BOUND, heartbeat)
            heartbeat_timer.start()

        elif self.path.endswith('destroy'):
            heartbeat_timer.cancel()
            de_allocate_vm('all')
        
        elif self.path.endwith('online'):
            inProgress_timer.cancel()
            inProgress = False

        else :
            # Convert json Unicode encoding to string
            vm = str(jsonMessage["vm"])
            stat = {"res_time": jsonMessage["res_time"]}; 
            self._insert(vm, stat)
            #self._printToFile(vm)
            if len(stat_table) < template.maxVM and check_high_load(vm):
                allocate_vm(1)
                inProgress = True
                inProgress_timer = threading.timer(INPROGRESS_BOUND, pull_inProgress)
                inProgress_timer.start()

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
