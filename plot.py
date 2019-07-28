import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5 import QtWidgets as QW


class CanvasCurve(FigureCanvas):
	def __init__(self, parent=None, width=2, height=1):
		self.fig = plt.figure(figsize=(width,height))
		FigureCanvas.__init__(self, self.fig)
		self.setParent(parent)
		FigureCanvas.setSizePolicy(self, QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		self.axs = []
		self.updh = [] # handles to be updated in every iteration
		self.figure_background()

		self.data = (np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0))

	def figure_background(self):
		self.axs.append( self.fig.add_axes([0,0,1,1]) ) # set the axis size to fill the figure

		# set axes preperties
		for ax in self.axs:
			# ax.set_axis_off()
			# ax.set_frame_on(True)
			ax.grid()
			ax.set_ylim([0,1])

	def figure_draw(self):
		self.figure_clear()

		ax = self.axs[0]

		# draw expected data
		x = self.data[2]
		y = self.data[3]
		self.updh += ax.plot(x, y, color='red') # ax.plot return a list of handles, not just one handle

		# draw real time data
		x = self.data[0]
		y = self.data[1]
		self.updh += ax.plot(x, y, color='blue')

		x1, x2, ran = np.min(x), np.max(x), 5.0
		ax.set_xlim( (x1, x1+ran) if (x2-x1<ran) else (x2-ran, x2) )

		self.draw()

	def figure_clear(self):
		while self.updh: self.updh.pop().remove() # clear every handle and delete the handle from the handle list


class CanvasAngle(FigureCanvas):
	def __init__(self, parent=None, width=1, height=1, scale=1):
		self.fig = plt.figure(figsize=(width,height))
		FigureCanvas.__init__(self, self.fig)
		self.setParent(parent)
		FigureCanvas.setSizePolicy(self, QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		self.axs = []
		self.updh = [] # handles to be updated in every iteration
		self.figure_background()

		self.data = (0,0,0)
		self.scale = scale

	def figure_background(self):
		self.axs.append( self.fig.add_axes([0,0,1,1]) ) # set the axis size to fill the figure

		# draw indicator lines at inclination angle 30, 60, 90
		ax = self.axs[0]
		PI = np.pi
		for r in (np.sin(PI/6), np.sin(PI/3), 1.0):
			x = r * np.cos( np.linspace(0, 2*PI, 180) )
			y = r * np.sin( np.linspace(0, 2*PI, 180) )
			ax.plot(x, y, color='black', ls='--')

		# set axes preperties
		for ax in self.axs:
			ax.set_axis_off()
			ax.set_frame_on(False)
			ax.axis('scaled')
			ax.axis([-1.2,1.2,-1.2,1.2])

	def figure_draw(self):
		# IMU data define:
		# coordinate: x -> front, y -> left, z -> up
		# positive direction: yaw -> turn right, pitch -> headup, roll -> left roll
		self.figure_clear()

		PI = np.pi
		# rescale the data so that they can all be treated as angles
		yaw, pitch, roll = [ PI/180*n for n in (self.data/self.scale) ]
		# limit the angles (-180<=yaw<=180, -90<=pitch<=90, -90<=roll<=90)
		if abs(yaw) > PI:		yaw = PI * np.sign(yaw)
		if abs(pitch) > PI/2:	pitch = PI/2 * np.sign(pitch)
		if abs(roll) > PI/2:	roll = PI/2 * np.sign(roll)

		ax = self.axs[0]
		# draw inclination
		x =-np.tan(pitch)/ (1+np.tan(pitch)**2+np.tan(roll)**2)**0.5 # the projection of unit vector on x axis
		y = np.tan(roll) / (1+np.tan(pitch)**2+np.tan(roll)**2)**0.5 # the projection of unit vector on y axis
		if (x**2+y**2)**0.5 < 0.1:	self.updh.append( ax.scatter(0, 0, c='red', s=6) ) # when the attitude is very upright, show a red point at the figure center
		else:	self.updh.append( ax.arrow(0, 0, -y, x, length_includes_head=True, lw=0, fc='black', width=0.04) ) # (-y, x) is because body frame should rotate to the figure frame
		# draw heading direction
		x, y = np.cos(-yaw), np.sin(-yaw) # -yaw is the angle between the heading direction and north, in a regular polar system
		head = 0.2 # ratio of the arrow head length to the vector length
		self.updh.append( ax.arrow(-y, x, -y*head, x*head, length_includes_head=True, lw=0, fc='red', width=head/4.5*(x**2+y**2)**0.5) ) # set the width so that the arrow only has head
		# self.updh.append( ax.text(-y*(head+1), x*(head+1), 'N', FontSize=6) )

		self.draw()

	def figure_clear(self):
		while self.updh: self.updh.pop().remove() # clear every handle and delete the handle from the handle list


class CanvasVeloc(FigureCanvas):
	def __init__(self, parent=None, width=1, height=1, scale=1):
		self.fig = plt.figure(figsize=(width,height))
		FigureCanvas.__init__(self, self.fig)
		self.setParent(parent)
		FigureCanvas.setSizePolicy(self, QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

		self.axs = []
		self.updh = [] # handles to be updated in every iteration
		self.figure_background()

		self.data = (0,0,0)
		self.scale = scale

	def figure_background(self):
		pass
	def figure_draw(self):
		pass
	def figure_clear(self):
		while self.updh: self.updh.pop().remove()


class MplWidget(QW.QWidget):
	def __init__(self, parent=None):
		super(MplWidget, self).__init__(parent)

	def setup(self, figtype):
		if	 figtype == 0:	self.mpl = CanvasCurve(self)
		elif figtype == 1:	self.mpl = CanvasAngle(self)
		elif figtype == 2:	self.mpl = CanvasAngle(self, scale=2)
		elif figtype == 3:	self.mpl = CanvasVeloc(self)
		elif figtype == 4:	self.mpl = CanvasVeloc(self)

		QW.QVBoxLayout(self).addWidget(self.mpl)

	def update(self, figdata):
		self.mpl.data = figdata
		self.mpl.figure_draw()

	





# if __name__ == '__main__':
# 	import sys
# 	app = QW.QApplication(sys.argv)
# 	ui = MplWidgetPoseture()
# 	# ui.mpl.start_dynamic_plot()
# 	ui.show()
# 	sys.exit(app.exec_())








# class CanvasAttiAngle(FigureCanvas):
# 	def __init__(self, parent=None, width=1, height=1):
# 		self.fig = plt.figure(figsize=(width,height))
# 		FigureCanvas.__init__(self, self.fig)
# 		self.setParent(parent)
# 		FigureCanvas.setSizePolicy(self, QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
# 		FigureCanvas.updateGeometry(self)

# 		self.axs = []
# 		self.updh = [] # handles to be updated in every iteration
# 		self.figure_background()

# 		self.data = (0,0,0)

# 	def figure_background(self):
# 		PI = np.pi

# 		self.axs.append( self.fig.add_axes([0,0,1,1]) ) # set the axis size to fill the figure

# 		# draw indicator lines at inclination angle 30, 60, 90
# 		ax = self.axs[0]
# 		for r in (np.sin(PI/6), np.sin(PI/3), 1.0):
# 			x = r * np.cos( np.linspace(0, 2*PI, 180) )
# 			y = r * np.sin( np.linspace(0, 2*PI, 180) )
# 			ax.plot(x, y, color='black', ls='--')

# 		# set axes preperties
# 		for ax in self.axs:
# 			ax.set_axis_off()
# 			ax.set_frame_on(False)
# 			ax.axis('scaled')
# 			ax.axis([-1.4,1.4,-1.4,1.4])

# 	def figure_draw(self):
# 		# IMU data define:
# 		# coordinate: x -> front, y -> left, z -> up
# 		# positive direction: yaw -> turn right, pitch -> headup, roll -> left roll
# 		self.figure_clear()

# 		PI = np.pi
# 		yaw, pitch, roll = [ PI/180*n for n in self.data ]

# 		ax = self.axs[0]
# 		# draw inclination
# 		x =-np.tan(pitch)/ (1+np.tan(pitch)**2+np.tan(roll)**2)**0.5 # the projection of unit vector on x axis
# 		y = np.tan(roll) / (1+np.tan(pitch)**2+np.tan(roll)**2)**0.5 # the projection of unit vector on y axis
# 		if (x**2+y**2)**0.5 < 0.1:	self.updh.append( ax.scatter(0, 0, c='red', s=6) ) # when the attitude is very upright, show a red point at the figure center
# 		else:	self.updh.append( ax.arrow(0, 0, -y, x, length_includes_head=True, lw=0, fc='black', width=0.04) ) # (-y, x) is because body frame should rotate to the figure frame
# 		# draw heading direction
# 		x, y = np.cos(yaw), np.sin(yaw) # yaw is the direction of north in body coordinate, supposing the body is originally heading to north
# 		scale = 0.2 # ratio of the arrow head length to the vector length
# 		self.updh.append( ax.arrow(-y, x, -y*scale, x*scale, length_includes_head=True, lw=0, fc='red', width=scale/4.5*(x**2+y**2)**0.5) ) # set the width so that the arrow only has head
# 		self.updh.append( ax.text(-y*(scale+1), x*(scale+1), 'N', FontSize=6) )

# 		self.draw()

# 	def figure_clear(self):
# 		while self.updh: self.updh.pop().remove() # clear every handle and delete the handle from the handle list


# class CanvasAngleVelo(FigureCanvas):
# 	def __init__(self, parent=None, width=1, height=1):
# 		self.fig = plt.figure(figsize=(width,height))
# 		FigureCanvas.__init__(self, self.fig)
# 		self.setParent(parent)
# 		FigureCanvas.setSizePolicy(self, QW.QSizePolicy.Expanding, QW.QSizePolicy.Expanding)
# 		FigureCanvas.updateGeometry(self)

# 		self.axs = []
# 		self.updh = [] # handles to be updated in every iteration
# 		self.figure_background()

# 		self.data = (0,0,0)

# 	def figure_background(self):
# 		PI = np.pi

# 		self.axs.append( self.fig.add_axes([0,0,1,1]) )

# 		# draw indicator lines at total angle velocity MAX_AV*1/3, MAX_AV*2/3, MAX_AV
# 		ax = self.axs[0]
# 		for r in (0.33, 0.66, 1.0):
# 			x = r * np.cos( np.linspace(0, 2*PI, 180) )
# 			y = r * np.sin( np.linspace(0, 2*PI, 180) )
# 			ax.plot(x, y, color='black', ls='--')

# 		# set axes preperties
# 		for ax in self.axs:
# 			ax.set_axis_off()
# 			ax.set_frame_on(False)
# 			ax.axis('scaled')
# 			ax.axis([-1.4,1.4,-1.4,1.4])

# 	def figure_draw(self):
# 		# IMU data define:
# 		# coordinate: x -> front, y -> left, z -> up
# 		# positive direction: yaw -> turn right, pitch -> headup, roll -> left roll
# 		self.figure_clear()

# 		PI = np.pi
# 		MAX_AV = 180.0
# 		yaw, pitch, roll = self.data

# 		ax = self.axs[0]
# 		# draw inclination velocity
# 		tot_av = (pitch**2+roll**2)**0.5
# 		scale = 1.0/MAX_AV if ( tot_av<=MAX_AV ) else 1.0/tot_av
# 		x, y = -pitch*scale, roll*scale # the direction and amplitude of inclination velocity
# 		if (x**2+y**2)**0.5 < 0.1:	self.updh.append( ax.scatter(0, 0, c='red', s=6) )
# 		else:	self.updh.append( ax.arrow(0, 0, -y, x, length_includes_head=True, lw=0, fc='black', width=0.04) )
# 		# draw heading velocity
# 		scale = 0.95*PI/MAX_AV if ( abs(yaw)<=MAX_AV ) else 0.95*PI/yaw # maximum angle of the pointer is +- 171 deg
# 		x, y = np.cos(-yaw*scale), np.sin(-yaw*scale) # -yaw is the direction of head turning velocity in regular polar system
# 		scale = 0.2
# 		self.updh.append( ax.arrow(-y, x, -y*scale, x*scale, length_includes_head=True, lw=0, fc='red', width=scale/4.5*(x**2+y**2)**0.5) )

# 		self.draw()

# 	def figure_clear(self):
# 		while self.updh: self.updh.pop().remove() # clear every handle and delete the handle from the handle list


