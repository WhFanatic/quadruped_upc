import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore as QC


class DynamicGraphWidget_curves(pg.GraphicsLayoutWidget):
	""" draw 12 figures on the widget """

	def __init__(self, parent=None):
		super(DynamicGraphWidget_curves, self).__init__(parent)

		self.ci.layout.setContentsMargins(0, 0, 0, 0)
		self.ci.layout.setSpacing(0)

		self.keys = ['LFX', 'RFX', 'LFD', 'RFD', 'LFK', 'RFK', 'LBX', 'RBX', 'LBD', 'RBD', 'LBK', 'RBK']
		self.figs = {}
		self.crvs = {}
		self.refs = {}
		self.ran = 5.0

		for key in self.keys:
			if self.keys.index(key) and not self.keys.index(key)%2: self.nextRow()

			fig = self.addPlot()
			fig.setRange(yRange=(-1,1))
			fig.setMouseEnabled(x=False, y=False)
			fig.disableAutoRange()
			fig.showGrid(x=True, y=True, alpha=0.5)
			fig.hideAxis('bottom')
			fig.hideAxis('left')
			fig.setTitle(key)

			self.figs[key] = fig
			self.crvs[key] = fig.plot([], [])
			self.refs[key] = fig.plot([], [], pen={'style':QC.Qt.DotLine})

	def update(self, time, data, ref_time=[], ref_data=[]):
		x1, x2, ran = np.min(time), np.max(time), self.ran
		xRange = (x1, x1+ran) if (x2-x1<ran) else (x2-ran, x2)
		for i in range(4):
			for j in range(3):
				key = self.keys[ j*2 + int(i/2)*6 + i%2 ]
				self.figs[key].setRange(xRange=xRange)
				self.crvs[key].setData(time, data[:,i,j])
				if len(ref_time): self.refs[key].setData(ref_time, ref_data[:,i,j])



class DynamicGraphWidget_angle(pg.GraphicsLayoutWidget):
	""" draw a meter figure on the widget """

	def __init__(self, parent=None):
		super(DynamicGraphWidget_angle, self).__init__(parent)

		self.ci.layout.setContentsMargins(0, 0, 0, 0)
		self.ci.layout.setSpacing(0)
		
		self.fig = self.addPlot()
		self.fig.setRange(xRange=(-1.2,1.2), yRange=(-1.2,1.2))
		self.fig.setMouseEnabled(x=False, y=False)
		self.fig.disableAutoRange()
		self.fig.hideAxis('bottom')
		self.fig.hideAxis('left')

		self.crv0 = self.fig.plot([], [], pen={'width':3, 'color':'w'})

		self.scale = 1.0 # the ratio of the data value (in general) to angle values (-180~180)

		for r in (0.5, 3**0.5/2, 1.0):	# draw indicator lines at inclination angle 30, 60, 90
			x = r * np.cos( np.linspace(0, 2*np.pi, 180) )
			y = r * np.sin( np.linspace(0, 2*np.pi, 180) )
			crv = self.fig.plot(x, y)
			crv.setPen(style=QC.Qt.DotLine)

	def update(self, yaw, pitch, roll):
		""" IMU data defined as follows: """
		""" coordinate: x -> front, y -> left, z -> up """
		""" positive direction: yaw -> turn right, pitch -> headup, roll -> roll left """

		PI = np.pi
		# rescale and limitate the data so that they can all be treated as angles
		alfa, beta, gama = np.array([yaw, pitch, roll]) * PI/180 / self.scale
		if abs(alfa) > PI:		alfa = PI * np.sign(alfa)	# -180 <= alfa <= 180
		if abs(beta) > PI/2:	beta = PI/2 * np.sign(beta)	# -90 <= beta <= 90
		if abs(gama) > PI/2:	gama = PI/2 * np.sign(gama)	# -90 <= gama <= 90

		# the projection of (unit vector erected on the body) on (the un-tumbled body system)
		x =-np.tan(beta) / (1+np.tan(beta)**2+np.tan(gama)**2)**0.5
		y = np.tan(gama) / (1+np.tan(beta)**2+np.tan(gama)**2)**0.5
		x, y = -y, x # rotate from the un-tumbled body system to the figrue system
		rad = np.arctan(y/-x) if x<0 else PI-np.arctan(y/x) if x>0 else PI/2*np.sign(y) # angle of arrow in figure system (left is 0 and clockwise is positive)
		
		if hasattr(self, 'arr1'):	self.fig.removeItem(self.arr1)
		if hasattr(self, 'arr2'):	self.fig.removeItem(self.arr2)

		rr = 1.15 # rescale the coordinate value to make the plot nice
		self.crv0.setData([0,x/rr], [0,y/rr])
		self.arr1 = pg.ArrowItem(pen=None, brush='w', headLen=8, tipAngle=45, angle=rad/PI*180, pos=(x,y))
		self.arr2 = pg.ArrowItem(pen=None, brush='r', headLen=10, tipAngle=45, angle=alfa/PI*180+90, pos=(rr*np.sin(alfa), rr*np.cos(alfa))) # yaw is relative to north
		self.fig.addItem(self.arr1)
		self.fig.addItem(self.arr2)


class DynamicGraphWidget_veloc(pg.GraphicsLayoutWidget):
	def __init__(self, parent=None):
		super(DynamicGraphWidget_veloc, self).__init__(parent)
	def update(self, yaw, pitch, roll):
		pass


if __name__ == '__main__':
	""" this is just for debug """

	import sys
	from PyQt5 import QtWidgets as QW

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




class DynamicGraphWidget_curve(pg.GraphicsLayoutWidget):
	""" draw one figure on the widget. this class is depricated """
	def __init__(self, parent=None):
		super(DynamicGraphWidget_curve, self).__init__(parent)

		self.ci.layout.setContentsMargins(0, 0, 0, 0)
		self.ci.layout.setSpacing(0)

		self.fig = self.addPlot()
		self.fig.setRange(yRange=(-1,1))
		self.fig.setMouseEnabled(x=False, y=False)
		self.fig.disableAutoRange()
		self.fig.showGrid(x=True, y=True, alpha=0.5)
		self.fig.hideAxis('bottom')
		self.fig.hideAxis('left')

		self.crv = self.fig.plot([], [])
		self.crv0= self.fig.plot([], [], pen={'style':QC.Qt.DotLine})

		self.ran = 5.0

	def update(self, x, y, x0=[], y0=[]):
		x1, x2, ran = np.min(x), np.max(x), self.ran
		self.fig.setRange( xRange = (x1, x1+ran) if (x2-x1<ran) else (x2-ran, x2) )
		self.crv.setData(x, y)
		self.crv0.setData(x0, y0)














