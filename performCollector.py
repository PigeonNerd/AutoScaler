#!/usr/bin/python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os

""" 
    This class implements a CPU Performance Collector.
    The collector works as a http server. It recieves the periodical 
    updates from performance monitors on each VMs and put them into a
    Map
""" 


#Create custom HTTPRequestHandler class
class CPUStatusHandler(BaseHTTPRequestHandler):

    def __init__(self):
        self.stat_table = dict()
        self.period_boud = 5

    #handle GET command
    def do_GET(self):
         self.send_response(200)
         self.end_headers()

    #handle POST command
    def do_POST(self):
        self.send_response(201)
        self.end_headers()
        content_type = self.headers.getheader('Content-Type')
        content_len = self.headers.getheader('Content-Length')
        post_body = self.rfile.read(int(content_len))
        print 'body="%s"; type="%s"' % (post_body, content_type)


    
def run():
    print('http server is starting...')
    #ip and port of servr
    #by default http server port is 8080
    server_address = ('127.0.0.1', 8081)
    handle = CPUStatusHandler()
    httpd = HTTPServer(server_address, handle)
    print('http server is running...')
    httpd.serve_forever()
    
if __name__ == '__main__':
    run()