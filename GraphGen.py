from pychart import *
import json
import re
theme.get_options()
import sys

class Graph:
	def __init__(self, logfile, siegelog):
		self.data = []
		f = open(logfile, "r")
		for line in f.readlines():
			jsonMessage = json.loads(line.strip())
			self.data.append( (int(jsonMessage["time"]), int(jsonMessage["numVMs"]), float(jsonMessage["res_time"])) )
		f.close()
		
		self.data2 = []
		temp = []
		f = open(siegelog, "r")
		lines = f.readlines();
		lines = lines[1:]
		for line in lines:
			tokens = line.strip().split(",")
			for i in range(len(tokens)):
				tokens[i] = tokens[i].strip()
			temp.append(tokens)

		for i in range(len(temp)):
			temp[i][2] = float(temp[i][2])
			elapse = temp[i][2]
			if i > 0:	
				temp[i][2] += float(temp[i - 1][2])
			self.data2.append( ( temp[i][2] - 2 * elapse /1.0/3, float(temp[i][7]) ) )
			self.data2.append( ( temp[i][2] - elapse / 1.0 / 3, float(temp[i][7]) ) )
			self.data2.append( ( temp[i][2], float(temp[i][7]) ) )
			f.close()
			
	def drawRequestVsTime(self):
			tic = self.data2[2][0]
			xaxis = axis.X(format="/a-60/hL%d", tic_interval = tic, label="Time")
			yaxis = axis.Y(tic_interval = 0.5, label="Number of concurrent requests")
			ar = area.T(x_axis=xaxis, y_axis=yaxis, y_range=(0,None))
			plot = line_plot.T(label="p1", data=self.data2, ycol=1)
			ar.add_plot(plot)
			ar.draw()

	def drawVMVsTime(self):
			tic = self.data[-1][0] / 8
			xaxis = axis.X(format="/a-60/hL%d", tic_interval = tic, label="Time")
			yaxis = axis.Y(tic_interval = 1, label="Number of VMs")
			ar = area.T(x_axis=xaxis, y_axis=yaxis, y_range=(0,None))
			plot = line_plot.T(label="p2", data=self.data, ycol=1)
			ar.add_plot(plot)
			ar.draw()

	def drawResVsTime(self):
			tic = self.data[-1][0] / 8
			xaxis = axis.X(format="/a-60/hL%d", tic_interval = tic, label="Time")
			yaxis = axis.Y(tic_interval = 1, label="Response Time( Seconds )")
			ar = area.T(x_axis=xaxis, y_axis=yaxis, y_range=(0,None))
			plot = line_plot.T(label="p2", data=self.data, ycol=2)
			ar.add_plot(plot)
			ar.draw()

if __name__ == '__main__':
	g = Graph('log/load_1/collect.log', "log/load_1/siege.log")

	if sys.argv[1] == 'req':
		sys.stdout = open('RequestVsTime.pdf', 'w')
		g.drawRequestVsTime()
	elif sys.argv[1] == 'res':
		sys.stdout = open('ResVsTime.pdf', 'w')
		g.drawResVsTime()
	elif sys.argv[1] == "vm":
		sys.stdout = open('VmVsTime.pdf', 'w')
		g.drawVMVsTime()
	else:
		print "Wrong command, should be one of req, res, vm"
	

