import numpy as np
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC
import pyqtgraph as pg


class DynamicGraphWidget_curve(pg.GraphicsLayoutWidget):
	def __init__(self, parent=None):
		super(DynamicGraphWidget_curve, self).__init__(parent)

		self.fig = self.addPlot()
		self.fig.setRange(yRange=(0,1))
		self.fig.showGrid(x=True, y=True, alpha=0.5)

		self.crv = self.fig.plot([], [])
		self.crv0= self.fig.plot([], [], pen={'style':QC.Qt.DotLine})

		self.ran = 5.0

	def update(self, x, y, x0=[], y0=[]):
		x1, x2, ran = np.min(x), np.max(x), self.ran
		self.fig.setRange( xRange = (x1, x1+ran) if (x2-x1<ran) else (x2-ran, x2) )
		self.crv.setData(x, y)
		self.crv0.setData(x0, y0)

class DynamicGraphWidget_angle(pg.GraphicsLayoutWidget):
	def __init__(self, parent=None):
		super(DynamicGraphWidget_angle, self).__init__(parent)

		self.fig = self.addPlot()
		self.fig.setRange(xRange=(-1.2,1.2), yRange=(-1.2,1.2))
		self.fig.hideAxis('bottom')
		self.fig.hideAxis('left')

		self.crv0 = self.fig.plot([], [], pen={'width':3, 'color':'w'})

		# draw indicator lines at inclination angle 30, 60, 90
		for r in (0.5, 3**0.5/2, 1.0):
			x = r * np.cos( np.linspace(0, 2*np.pi, 180) )
			y = r * np.sin( np.linspace(0, 2*np.pi, 180) )
			crv = self.fig.plot(x, y)
			crv.setPen(style=QC.Qt.DotLine)

		self.scale = 1.0

		self.update(45,45,45)

	def update(self, yaw, pitch, roll):
		# IMU data define:
		# coordinate: x -> front, y -> left, z -> up
		# positive direction: yaw -> turn right, pitch -> headup, roll -> roll left

		PI = np.pi
		# rescale the data so that they can all be treated as angles
		alfa, beta, gama = [ n*PI/180/self.scale for n in (yaw, pitch, roll) ]
		# limit the angles (-180<=alfa<=180, -90<=beta<=90, -90<=gama<=90)
		if abs(alfa) > PI:		alfa = PI * np.sign(alfa)
		if abs(beta) > PI/2:	beta = PI/2 * np.sign(beta)
		if abs(gama) > PI/2:	gama = PI/2 * np.sign(gama)

		# the projection of (unit vector erected on the body) on (the un-tumbled body system)
		x =-np.tan(beta) / (1+np.tan(beta)**2+np.tan(gama)**2)**0.5
		y = np.tan(gama) / (1+np.tan(beta)**2+np.tan(gama)**2)**0.5
		x, y = -y, x # rotate from the un-tumbled body system to the figrue system
		rad = np.arctan(y/-x) if x<0 else PI-np.arctan(y/x) if x>0 else PI/2*np.sign(y) # angle of arrow in figure system (left if 0 and clockwise is positive)
		
		if hasattr(self, 'arr1'):	self.fig.removeItem(self.arr1)
		if hasattr(self, 'arr2'):	self.fig.removeItem(self.arr2)
		self.crv0.setData([0,x], [0,y])
		self.arr1 = pg.ArrowItem(pen=None, brush='w', tipangle=30, angle=rad/PI*180, pos=(x,y))
		self.arr2 = pg.ArrowItem(pen=None, brush='r', tipAngle=45, angle=alfa/PI*180+90, pos=(1.1*np.sin(alfa), 1.1*np.cos(alfa))) # yaw is relative to north
		self.fig.addItem(self.arr1)
		self.fig.addItem(self.arr2)


class DynamicGraphWidget_veloc(pg.GraphicsLayoutWidget):
	def __init__(self, parent=None):
		super(DynamicGraphWidget_veloc, self).__init__(parent)
	def update(self, yaw, pitch, roll):
		pass


if __name__ == '__main__':
	import sys
	app = QW.QApplication(sys.argv)

	# ui = DynamicGraphWidget_curve()
	# x = np.linspace(0,2*np.pi,100)
	# y = np.sin(2*x)
	# x0, y0 = x, -y
	# ui.update(x,y,x0,y0)

	ui = DynamicGraphWidget_angle()
	ui.update(45,45,45)

	ui.show()

	sys.exit(app.exec_())




















