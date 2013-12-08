from pychart import *
import json
theme.get_options()


class Graph:
	def __init__(self, logfile):
		self.data = []
		f = open(logfile, "r")
		for line in f.readlines():
			jsonMessage = json.loads(line.strip())
			self.data.append( (int(jsonMessage["time"]), int(jsonMessage["numVMs"]), int(jsonMessage["res_time"])) )
						
	def draw(self):
			xaxis = axis.X(format="/a-60/hL%d", tic_interval = 4, label="Number of VMs")
			yaxis = axis.Y(tic_interval = 4, label="Time")
			ar = area.T(x_axis=xaxis, y_axis=yaxis, y_range=(0,None))
			plot = line_plot.T(label="Number of VMs vs. Time", data=self.data, ycol=1)
			ar.add_plot(plot)
			ar.draw()

if __name__ == '__main__':

	 g = Graph('test.log')
	 g.draw()


