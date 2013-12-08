#!/usr/bin/python

import BaseHTTPServer

"""
  This class implements a simple HTTP server for debugging
  purpose ONLY. It helps to facilitate the unit/functional tests.
"""
class SimpleHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        self.send_response(201)
        self.end_headers()
        content_type = self.headers.getheader('Content-Type')
        content_len = self.headers.getheader('Content-Length')
        post_body = self.rfile.read(int(content_len))
        print 'body="%s"; type="%s"' % (post_body, content_type)

if __name__ == '__main__':
    try:
        server = BaseHTTPServer.HTTPServer(("0.0.0.0", 10088), SimpleHandler)
        print 'HTTP Server is Running ... '
        server.serve_forever()
    except KeyboardInterrupt:
        print 'Server is Shutting Down ... '
        server.shutdown()
