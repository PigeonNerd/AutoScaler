from pychart import *
import json
import re
theme.get_options()


class Graph:
	def __init__(self, logfile, siegelog):
		self.data = []
		f = open(logfile, "r")
		for line in f.readlines():
			jsonMessage = json.loads(line.strip())
			self.data.append( (int(jsonMessage["time"]), int(jsonMessage["numVMs"]), int(jsonMessage["res_time"])) )
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
			
			

	def draw(self):
			xaxis = axis.X(format="/a-60/hL%d", tic_interval = 180, label="Value")
			yaxis = axis.Y(tic_interval = 2, label="Time")
			ar = area.T(x_axis=xaxis, y_axis=yaxis, y_range=(0,None))
			plot = line_plot.T(label="Number of VMs vs. Time", data=self.data, ycol=1)

			plot2 = line_plot.T(label="Number of concurent requests vs. Time", data=self.data2, ycol=1)

			ar.add_plot(plot2)
			ar.draw()

if __name__ == '__main__':

	 g = Graph('test.log', "log/siege.log")
	 


