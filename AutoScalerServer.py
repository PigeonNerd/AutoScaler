#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
import json

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
#Stat file name
stat_file = "collect.log"

#Create custom HTTPRequestHandler class
class TomcatStatusHandler(BaseHTTPRequestHandler):

    #handle POST command
    def do_POST(self):
        self.send_response(201)
        self.end_headers()
        content_type = self.headers.getheader('Content-Type')
        content_len = self.headers.getheader('Content-Length')
        post_body = self.rfile.read(int(content_len))
        #print 'body="%s"; type="%s"' % (post_body, content_type)
        jsonMessage = json.loads(post_body)
        # Convert json Unicode encoding to string
        vm = str(jsonMessage["vm"])
        stat = {"res_time": jsonMessage["res_time"]}; 
        self._insert(vm, stat)
        self._printToFile(vm)

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
