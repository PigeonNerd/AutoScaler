#!/usr/bin/python
import urllib2
import json
import sys
import re

collector_addr = "http://localhost:10088/"

class Template:
	 def __init__(self, maxVM, minVM, imagePath, targetTime):
	 	##self.collector_addr = "http://auto-scaler-server:10086/"
	 	self.maxVM = int(maxVM)
	 	self.minVM = int(minVM)
	 	self.imagePath = imagePath
	 	self.targetTime = float(targetTime)

	 def makeJson(self):
	 	return json.dumps({"maxVM": self.maxVM, "minVM": self.minVM, 
	 		"imagePath": self.imagePath, "targetTime": self.targetTime})

	 def printTemplate(self):
	 	print "max VMs = %d\nmin VMs = %d\nimage path = %s\nresponse target time = %s" % (self.maxVM, self.minVM, self.imagePath, self.targetTime)

def send(data, action):
 	req = urllib2.Request(collector_addr + action)
 	req.add_header('Content-Type', 'application/json')
 	req.add_header('User-Agent', 'tomcat-monitor/0.0.1')
 	req.add_data(data)
 	try:
 		urllib2.urlopen(req)
 	except urllib2.URLError as ue:
 		print ue.reason
 	except urllib2.HTTPError as he:
 		print "%s - %s" % (he.code, he.reason)

def afterColon( line ):
	return line.partition(":")[2].strip()


def instantiate(filePath):
	f = open(filePath)
	lines = f.readlines()
	temp = Template(afterColon(lines[0]), afterColon(lines[1]), afterColon(lines[2]), afterColon(lines[3]))
	f.close()
	send(temp.makeJson(), "instantiate")

def destroy(filePath):
	f = open(filePath)
	lines = f.readlines()
	temp = Template(afterColon(lines[0]), afterColon(lines[1]), afterColon(lines[2]), afterColon(lines[3]), )
	f.close()
	send(temp.makeJson(), "destroy")


if __name__ == '__main__':
	globals()[sys.argv[1]](sys.argv[2])
