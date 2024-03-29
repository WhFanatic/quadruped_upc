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


	@pyqtSlot(int)
	def on_comboBox_currentIndexChanged(self):
		""" when a gait is chosen, show the corresponding parameters """
		self.set_text(col1=False, col2=True)

	@pyqtSlot()
	def on_pushButton_4_clicked(self):
		""" set the left column to default parameters """
		para_temp = ParameterPackage() # default parameters loaded as soon as this class is created
		key = 'init'
		self.para.data[key][:] = para_temp.data[key]
		self.set_text(col1=True, col2=False)

	@pyqtSlot()
	def on_pushButton_3_clicked(self):
		""" set the right column to default parameters """
		para_temp = ParameterPackage() # default parameters loaded as soon as this class is created
		key = self.gait_keys[self.comboBox.currentIndex()]
		self.para.data[key][:] = para_temp.data[key]
		self.set_text(col1=False, col2=True)

	""" every time finishing editing the text box, save the number if it is valid """
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
		self.widget_2.scale = 2.0
		for key in self.widget_5.figs.keys(): # set the title of foot end force figures to LFX, LFY, LFZ, ...
			if key[-1] == 'D': self.widget_5.figs[key].setTitle(key[:2]+'Y')
			if key[-1] == 'K': self.widget_5.figs[key].setTitle(key[:2]+'Z')

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
		self.timer0 = QC.QTimer() # Check connection state
		self.timer1 = QC.QTimer() # Communication (receive data)

		self.timer0.timeout.connect(self.checkConnection)
		self.timer1.timeout.connect(self.hear)

		self.timer0.start(1000) # check connection state every 1 second, start as soon as the UI is launched
		self.timer1.setInterval(40)

########## set up slots ##########

##### connection #####
	@pyqtSlot()
	def on_pushButton_5_clicked(self):
		""" connect """
		self.client.serverIP = self.lineEdit_7.text()
		self.client.open()
		self.checkConnection()

	@pyqtSlot()
	def on_pushButton_6_clicked(self):
		""" disconnect """
		self.client.close()
		self.checkConnection()
######################

##### parameter setting #####
	@pyqtSlot()
	def on_pushButton_3_clicked(self):
		""" pop out the dialog for parameter setting """
		self.dialpose.para.decode('copy', datacopy=self.para.data)
		self.dialpose.set_text()
		self.dialpose.show()

	@pyqtSlot() # no reponse using @pyqtSlot, do not know why..., so this function is explicitly connected to self.dialpose
	def on_dialpose_accepted(self):
		""" save and send out the parameters if the 'save' button is clicked """
		self.para.decode('copy', datacopy=self.dialpose.para.data)
		self.para.save()
		self.client.send(self.prot.collect(typ=0x04, ack=0x04))
#############################

##### command buttons #####
	@pyqtSlot()
	def on_pushButton_11_clicked(self):
		""" send walk gait command """
		self.comd.switch, self.comd.gait, self.comd.rc = 0x00, 0x01, 0x00
		self.client.send(self.prot.collect(typ=0x03, ack=0x02))
###########################

##### figure tab #####
	@pyqtSlot(int)
	def on_tabWidget_currentChanged(self):
		self.update_figure_1()
	@pyqtSlot(int)
	def on_tabWidget_2_currentChanged(self):
		self.update_figure_2()
######################


########## other methods ##########

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
		# self.client.interact(self.prot.process)	# this do not dump any frame
		self.prot.distrib(self.client.recv())	# this returns the newest frame and dump the others
		if self.prot.cnt > last_cnt:
			if self.prot.cnt % 5 == 0:	self.update_figdata()	# set different update frequencies and phases to stagger these time-consuming operations
			if self.prot.cnt % 5 == 1:	self.update_figure_2()	# meter figures should update more frequently to look smooth
			if self.prot.cnt % 15== 3:	self.update_figure_1()

	def update_figdata(self):
		""" update figure data (only data, not figure) """
		if not self.sens.checkBufferEmpty():
			self.datashow.decode('copy', datacopy=self.sens.filter())
			if self.datashow.checkBufferFull():	self.datashow.bufferShift()
			self.datashow.bufferIn()

	def update_figure_1(self):
		""" refresh curve figures """
		if not self.datashow.checkBufferEmpty():
			buf = self.datashow.bufferGet()
			idx = self.tabWidget.currentIndex()
			if idx == 0:	self.widget.update(buf['forc_time'], buf['forc'])
			elif idx == 1:	self.widget_4.update(buf['disp_time'], buf['disp'])
			elif idx == 2:	self.widget_5.update(buf['foot_time'], buf['foot'])

	def update_figure_2(self):
		""" refresh meter figures """
		if not self.datashow.checkBufferEmpty():
			frame = self.datashow.last()
			idx = self.tabWidget_2.currentIndex()
			if idx == 0:
				self.widget_3.update(*frame['imu'][0])
				self.widget_2.update(*frame['imu'][1])
			elif idx == 1:
				pass





