# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets as QW
from PyQt5 import QtCore as QC
from PyQt5.QtCore import pyqtSlot

from uifiles import interface_Main
from uifiles import interface_PoseParam
from protocol import Protocol, SensorPackage, ParameterPackage
from communication import Client


class DialogPose(QW.QDialog, interface_PoseParam.Ui_Dialog):
	def __init__(self):
		super(QW.QDialog, self).__init__()
		self.setupUi(self)

		self.para = ParameterPackage()
		self.gait_keys = ['walk', 'trot', 'climb', 'obstacle', 'jump', 'run'] # key list of ParameterPackage.data, according to the order of combobox


	@pyqtSlot(int) # gait chosen
	def on_comboBox_currentIndexChanged(self):
		self.set_text(col1=False, col2=True)

	@pyqtSlot() # left column set to default parameters
	def on_pushButton_4_clicked(self):
		para_temp = ParameterPackage() # default parameters loaded as soon as this class is created
		key = 'init'
		self.para.data[key][:] = para_temp.data[key]
		self.set_text(col1=True, col2=False)

	@pyqtSlot() # right column set to default parameters
	def on_pushButton_3_clicked(self):
		para_temp = ParameterPackage() # default parameters loaded as soon as this class is created
		key = self.gait_keys[self.comboBox.currentIndex()]
		self.para.data[key][:] = para_temp.data[key]
		self.set_text(col1=False, col2=True)


	@pyqtSlot()
	def on_lineEdit_editingFinished(self):
		try:	self.para.data['init'][0] = float( self.lineEdit.text() )
		except:	pass
	@pyqtSlot()
	def on_lineEdit_2_editingFinished(self):
		try:	self.para.data['init'][1] = float( self.lineEdit_2.text() )
		except:	pass
	@pyqtSlot()
	def on_lineEdit_3_editingFinished(self):
		try:	self.para.data['init'][2] = float( self.lineEdit_3.text() )
		except:	pass
	@pyqtSlot()
	def on_lineEdit_4_editingFinished(self):
		try:	self.para.data[self.gait_keys[self.comboBox.currentIndex()]][0] = float( self.lineEdit_4.text() )
		except:	pass
	@pyqtSlot()
	def on_lineEdit_5_editingFinished(self):
		try:	self.para.data[self.gait_keys[self.comboBox.currentIndex()]][1] = float( self.lineEdit_5.text() )
		except:	pass
	@pyqtSlot()
	def on_lineEdit_6_editingFinished(self):
		try:	self.para.data[self.gait_keys[self.comboBox.currentIndex()]][2] = float( self.lineEdit_6.text() )
		except:	pass


	def set_text(self, col1=True, col2=True):
		if col1:
			self.lineEdit.setText( str(self.para.data['init'][0]) )
			self.lineEdit_2.setText( str(self.para.data['init'][1]) )
			self.lineEdit_3.setText( str(self.para.data['init'][2]) )
		if col2:
			key = self.gait_keys[self.comboBox.currentIndex()]
			self.lineEdit_4.setText( str(self.para.data[key][0]) )
			self.lineEdit_5.setText( str(self.para.data[key][1]) )
			self.lineEdit_6.setText( str(self.para.data[key][2]) )





class MainWindow(QW.QMainWindow, interface_Main.Ui_MainWindow):
	def __init__(self):
		super(QW.QMainWindow, self).__init__()
		self.setupUi(self)


		# set up dynamic figures
		self.widget_group1 = [
			# force
			[	[self.widget, self.widget_5, self.widget_7],			# LF X | D | K
				[self.widget_4, self.widget_6, self.widget_8],			# RF X | D | K
				[self.widget_9, self.widget_11, self.widget_13],		# LB X | D | K
				[self.widget_10, self.widget_12, self.widget_15]	],	# RB X | D | K
			# displacement
			[	[self.widget_24, self.widget_25, self.widget_26],		# LF X | D | K
				[self.widget_14, self.widget_16, self.widget_17],		# RF X | D | K
				[self.widget_18, self.widget_19, self.widget_20],		# LB X | D | K
				[self.widget_21, self.widget_22, self.widget_23]	],	# RB X | D | K
			# footend force
			[	[self.widget_39, self.widget_40, self.widget_41],		# LF X | D | K
				[self.widget_29, self.widget_30, self.widget_31],		# RF X | D | K
				[self.widget_32, self.widget_33, self.widget_34],		# LB X | D | K
				[self.widget_36, self.widget_37, self.widget_38]	]	# RB X | D | K
		]

		self.widget_2.scale = 2.0

		# set up attributes
		self.client = Client()
		self.connected = False

		self.dialpose = DialogPose()
		self.dialpose.accepted.connect(self.on_dialpose_accepted)

		self.prot = Protocol()
		self.sens = self.prot.sens
		self.stat = self.prot.stat
		self.comd = self.prot.comd
		self.para = self.prot.para
		self.datashow = SensorPackage(buflen_max=25)


		# set up timers
		self.timer0 = QC.QTimer() # control the frequency of checking connection state
		self.timer1 = QC.QTimer() # control the frequency of communication (receiving data)

		self.timer0.timeout.connect(self.checkConnection)
		self.timer1.timeout.connect(self.hear)

		self.timer0.start(1000) # check connection state every 1 second, start as soon as the UI is launched
		self.timer1.setInterval(40)


	### set up slots

	## connection
	@pyqtSlot() # connect
	def on_pushButton_5_clicked(self):
		self.client.serverIP = self.lineEdit_7.text()
		self.client.open()
		self.checkConnection()

	@pyqtSlot() # disconnect
	def on_pushButton_6_clicked(self):
		self.client.close()
		self.checkConnection()

	## parameter setting
	@pyqtSlot() # set parameters
	def on_pushButton_3_clicked(self):
		self.dialpose.para.decode('copy', datacopy=self.para.data)
		self.dialpose.set_text()
		self.dialpose.show()

	@pyqtSlot() # save parameters
	def on_dialpose_accepted(self): # no reponse using @pyqtSlot, do not know why...
		self.para.decode('copy', datacopy=self.dialpose.para.data)
		self.para.save()
		self.client.send(self.prot.collect(typ=0x04, ack=0x04))

	## command buttons
	@pyqtSlot()
	def on_pushButton_11_clicked(self):
		self.comd.switch, self.comd.gait, self.comd.rc = 0x00, 0x01, 0x00
		self.client.send(self.prot.collect(typ=0x03, ack=0x02))


	def checkConnection(self):
		connected = self.client.get_connection_state()
		connection_changed = self.connected != connected
		self.connected = connected

		if connection_changed and connected:
			self.sens = self.prot.sens = SensorPackage() # if reconnected, new log files are created and old buffers are dumped
			self.timer1.start()
			print("Start hearing ...")
			self.label_9.setText('Connected')
		elif connection_changed and not connected:
			self.timer1.stop()
			print("Hearing over. Total %i frames heard."%self.prot.cnt)
			self.label_9.setText('Disconnected')

	def hear(self):
		last_cnt = self.prot.cnt
		# self.client.interact(self.prot.process)
		self.prot.distrib(self.client.recv())
		if self.prot.cnt > last_cnt:
			if self.prot.cnt % 5 == 0:	self.update_figdata()
			if self.prot.cnt % 5 == 0:	self.update_figure()

	def update_figdata(self):	# update figure data (only data, not figure)
		if not self.sens.checkBufferEmpty():
			self.datashow.decode('copy', datacopy=self.sens.filter())
			if self.datashow.checkBufferFull():	self.datashow.bufferShift()
			self.datashow.bufferIn()

	def update_figure(self):	# refresh figures
		if not self.datashow.checkBufferEmpty():
			frame = self.datashow.last()
			buf = self.datashow.bufferGet()

			key = ('forc', 'disp', 'foot')[self.tabWidget.currentIndex()]
			widgets_curve = self.widget_group1[self.tabWidget.currentIndex()]
			for i in range(4):
				for j in range(3):
					widgets_curve[i][j].update(*[
						buf[key+'_time'], buf[key][:,i,j],		# real data
						buf[key+'_time'], buf[key][:,i,j]-0.1	# expected data
					])

			if self.tabWidget_2.currentIndex() == 0:
				self.widget_3.update(*frame['imu'][0])
				self.widget_2.update(*frame['imu'][1])
			elif self.tabWidget_2.currentIndex() == 1:
				pass





