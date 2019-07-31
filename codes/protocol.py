# -*- coding: utf-8 -*-
import numpy as np
import time
import os
from struct import pack, unpack


class SensorPackage():
	def __init__(self, buflen_max=500):
		# data dictionary. store 1 frame of data and their conrresponding time (time is also treated as data)
		self.data = {
			'forc': np.zeros([4,3]), # hydraulic cylinder force ( dim0: 4 legs [LF | RF | LB | RB]; dim1: 3 joints )
			'disp': np.zeros([4,3]), # hydraulic cylinder displacement ( dim0: 4 legs; dim1: 3 joints )
			'foot': np.zeros([4,3]), # foot end force ( dim0: 4 feet, dim1: xyz; dim2: [time | data] )
			'imu' : np.zeros([3,3]), # attitude sensor ( dim0: [attitude angle | angular velocity | acceleration], dim1: [yaw | pitch | roll] or xyz )
			'forc_time': 0.0,
			'disp_time': 0.0,
			'foot_time': 0.0,
			'imu_time' : 0.0	}

		# mark which term is updated and should be added into data buffer
		self.bufinflag = { key:False for key in self.data.keys() } # bufferIn() and encode() will set all bufinflags to False

		# data buffer, store every frame of data up to a maximum length, for file writing
		self.buflen_max = buflen_max
		self.buflen = { key:0 for key in self.data.keys() } # keep track on the length of every term in dictionary. This length is also the index of the next element to be added
		self.data_buf = { key:np.zeros([self.buflen_max, *np.shape(self.data[key])]) for key in self.data.keys() } # this is equivalent to: self.data_buf = { 'forc': np.zeros([self.buflen_max,4,3]), ... }

		# record all received data in local files, named by local time
		file_prefix = time.strftime("%y%m%d%H%M%S", time.localtime())
		self.filenames = { key:'log_%s_%s.txt'%(file_prefix, key) for key in  self.data.keys()}
		self.filepath = '../log/'
		if not os.path.exists(self.filepath): os.mkdir(self.filepath)

	def process(self, datastring):
		if not self.checkDataString(datastring): return
		self.decode(datastring)
		if self.checkBufferFull(): self.bufferOut()
		self.bufferIn()

	def decode(self, datastring, datacopy=None):
		if datastring == b'test':
			self.decode('copy', datacopy=self.test())
		elif datastring == 'copy':
			for key in self.data.keys():		self.data[key] = datacopy[key]
			for key in self.bufinflag.keys():	self.bufinflag[key] = True
		else:
			flag, = unpack( 'B', datastring[0:1] )
			idx = 1
			if flag & 0x01:
				self.bufinflag['forc'], self.bufinflag['forc_time'] = True, True
				self.data['forc_time'], = unpack( 'f', datastring[idx:idx+4] )
				self.data['forc'][:] = np.reshape( unpack('12f', datastring[idx+4:idx+52]), [4,3] )
				idx += 52
			if flag & 0x02:
				self.bufinflag['disp'], self.bufinflag['disp_time'] = True, True
				self.data['disp_time'], = unpack( 'f', datastring[idx:idx+4] )
				self.data['disp'][:] = np.reshape( unpack('12f', datastring[idx+4:idx+52]), [4,3] )
				idx += 52
			if flag & 0x04:
				self.bufinflag['foot'], self.bufinflag['foot_time'] = True, True
				self.data['foot_time'], = unpack( 'f', datastring[idx:idx+4] )
				self.data['foot'][:] = np.reshape( unpack('12f', datastring[idx+4:idx+52]), [4,3] )
				idx += 52
			if flag & 0x08:
				self.bufinflag['imu'], self.bufinflag['imu_time'] = True, True
				self.data['imu_time'], = unpack( 'f', datastring[idx:idx+4] )
				self.data['imu'][:] = np.reshape( unpack('9f', datastring[idx+4:idx+40]), [3,3] )
				idx += 40

	def encode(self):
		flag = 0x00
		if self.bufinflag['forc']:	flag = flag | 0x01
		if self.bufinflag['disp']:	flag = flag | 0x02
		if self.bufinflag['foot']:	flag = flag | 0x04
		if self.bufinflag['imu'] :	flag = flag | 0x08

		datastring = pack('B', flag)
		if flag & 0x01:	datastring += pack('f', self.data['forc_time']) + pack( '12f', *np.ravel(self.data['forc']) )
		if flag & 0x02:	datastring += pack('f', self.data['disp_time']) + pack( '12f', *np.ravel(self.data['disp']) )
		if flag & 0x04:	datastring += pack('f', self.data['foot_time']) + pack( '12f', *np.ravel(self.data['foot']) )
		if flag & 0x08:	datastring += pack('f', self.data['imu_time'] ) + pack( '9f' , *np.ravel(self.data['imu' ]) )

		for key in self.bufinflag.keys():	self.bufinflag[key] = False

		return datastring

	def bufferIn(self): # add the current frame to the buffer. Attention: must check whether the buffer is full before operation
		for key in self.data.keys():
			if self.bufinflag[key]:
				self.data_buf[key][self.buflen[key]] = self.data[key]
				self.buflen[key] += 1
				self.bufinflag[key] = False

	def bufferOut(self): # write the buffer to file and reset the buffer state (in case the buffer is full)
		for key in self.data.keys():
			if self.buflen[key] == self.buflen_max: # only the full-buffer terms will be written
				with open(self.filepath+self.filenames[key], 'a') as fp:
					for frame in self.data_buf[key]:
						fp.write( '\t'.join(['%.18e'%n for n in np.ravel(frame)]) + '\n' )

				self.buflen[key] = 0
				print(self.filenames[key]+' updated')
		

	def checkDataString(self, datastring):
		if datastring in ('copy', b'test'):
			return True
		elif type(datastring) == bytes and len(datastring) >= 1:
			flag, = unpack( 'B', datastring[0:1] )
			totlen = 1
			if flag & 0x01: totlen += 52
			if flag & 0x02: totlen += 52
			if flag & 0x03: totlen += 52
			if flag & 0x04: totlen += 40

			if totlen == len(datastring):
				return True
			else:
				print('Sensor data length dose not match !')
				return False
		else:
			print('Invalid sensor data !')
			return False

	def checkBufferFull(self): # if any buffer is full, either bufferOut() or bufferShift() should be called before next bufferIn()
		return ( self.buflen_max in self.buflen.values() )

	def checkBufferEmpty(self): # if any buffer is empty, filter() and last() cannot be called
		return ( 0 in self.buflen.values() )

##### these two methods are for dynamic figure data #####
	def bufferShift(self): # shift the buffer one frame backward (in case the buffer is full)
		for key in self.data.keys():
			if self.buflen[key] == self.buflen_max:
				self.data_buf[key][:] = np.roll(self.data_buf[key], -1, axis=0)
				self.buflen[key] -= 1

	def filter(self, filter_size=5): # generate filtered data by averaging the newest 5 frames. Attention: must check whether the buffer is empty before operation
		filter_range = { key:range( max(self.buflen[key]-filter_size, 0), self.buflen[key] ) for key in self.data.keys() }
		return { key:np.mean( self.data_buf[key][filter_range[key]], axis=0 ) for key in self.data.keys() }
#########################################################

	def test(self): # generate random numbers as test data
		test_data = { key:np.random.rand(*np.shape(self.data[key])) for key in self.data.keys() }
		test_data['imu'][0] = test_data['imu'][0] * 180.0 - 90
		test_data['imu'][1] = test_data['imu'][1] * 180.0 * 2 - 180.0
		for key in test_data.keys():
			if 'time' in key:	test_data[key] = time.time()
		return test_data

	def last(self): # return the last frame in data_buf. Attention: must check whether the buffer is full before operation
		return { key:self.data_buf[key][self.buflen[key]-1] for key in self.data.keys() }

	def bufferGet(self):
		return { key:self.data_buf[key][:self.buflen[key]] for key in self.data.keys() }


class StatePackage():
	def __init__(self):
		self.basic = 0x00
		self.gait = 0x00
	def process(self):
		pass
	def decode(self, datastring):
		self.basic, self.gait = unpack( '2B', datastring )
	def encode(self):
		return pack( '2B', self.basic, self.gait )


class CommandPackage():
	def __init__(self):
		self.switch = 0x00
		self.gait = 0x00
		self.rc = 0x00

	def process(self):
		pass
	def decode(self, datastring):
		self.switch, self.gait, self.rc = unpack( '3B', datastring )
	def encode(self):
		return pack( '3B', self.switch, self.gait, self.rc )


class ParameterPackage():
	def __init__(self):
		self.data = {
			'init':	np.zeros(3),
			'walk':	np.zeros(3),
			'trot':	np.zeros(3),
			'climb':np.zeros(3),
			'obstacle':	np.zeros(3),
			'jump':	np.zeros(3),
			'run':	np.zeros(3)	}

		file_prefix = time.strftime("%y%m%d%H%M%S", time.localtime())
		self.default_file = 'para_default.txt'
		self.current_file = 'para_%s.txt'%file_prefix
		self.filepath = '../para/'
		if not os.path.exists(self.filepath): os.mkdir(self.filepath)
		try: self.load(self.default_file)
		except IOError: self.save(self.default_file)

	def decode(self, datastring, datacopy=None):
		if datastring == 'copy':
			for key in self.data.keys(): self.data[key][:] = datacopy[key]
		else:
			flag, = unpack( 'B', datastring[0:1] )
			if flag == 0x01:
				self.data['init'][:]	= unpack( '3f', datastring[1 :13] )
				self.data['walk'][:]	= unpack( '3f', datastring[13:25] )
				self.data['trot'][:]	= unpack( '3f', datastring[25:37] )
				self.data['climb'][:]	= unpack( '3f', datastring[37:49] )
				self.data['obstacle'][:]= unpack( '3f', datastring[49:61] )
				self.data['jump'][:]	= unpack( '3f', datastring[61:73] )
				self.data['run'][:]		= unpack( '3f', datastring[73:85] )

	def encode(self):
		datastring = b'\x01'
		datastring += pack( '3f', *np.ravel(self.data['init']) )
		datastring += pack( '3f', *np.ravel(self.data['walk']) )
		datastring += pack( '3f', *np.ravel(self.data['trot']) )
		datastring += pack( '3f', *np.ravel(self.data['climb']) )
		datastring += pack( '3f', *np.ravel(self.data['obstacle']) )
		datastring += pack( '3f', *np.ravel(self.data['jump']) )
		datastring += pack( '3f', *np.ravel(self.data['run']) )
		return datastring

	def load(self, filename=None):
		with open(self.filepath + (filename if filename else self.current_file), 'r') as fp:
			for line in fp:
				if '#' in line:	line = line[:line.index('#')]
				line = line.strip()

				if '$' in line:
					key = line[line.index('$')+1:].strip()
					values = line[:line.index('$')].strip().split()
					self.data[key][:] = [ float(s) for s in values ]

	def save(self, filename=None):
		with open(self.filepath + (filename if filename else self.current_file), 'w') as fp:
			for key in self.data.keys():
				fp.write( '\t'.join(['%.18e'%n for n in self.data[key]]) + '\t$ %s\n'%key )


# in main charge of all the communication
class Protocol():
	def __init__(self):
		self.ver = 0x01
		self.ack = 0x00
		self.typ = 0x00
		self.data = b''

		self.sens = SensorPackage()
		self.stat = StatePackage()
		self.comd = CommandPackage()
		self.para = ParameterPackage()

		self.cnt = 0 # how many data packages have been processed

	def distrib(self, datastring):	# for receive in communication
		if type(datastring) == bytes and len(datastring) >= 3:
			self.decode(datastring)
			self.cnt += 1

	def collect(self, typ, ack):	# for send in communication
		self.typ = typ
		self.ack = ack if ack else 0x00
		return self.encode()

	def process(self, datastring):	# for interact in communication
		self.distrib(datastring)
		if self.ack: return self.collect(typ=self.ack, ack=0x00)
		else: return None

	def decode(self, datastring):
		self.ver, = unpack( 'B', datastring[0:1] )
		self.ack, = unpack( 'B', datastring[1:2] )
		self.typ, = unpack( 'B', datastring[2:3] )
		self.data = datastring[3:]

		if self.typ == 0x01:	self.sens.process(self.data)
		elif self.typ == 0x02:	self.stat.decode(self.data)
		elif self.typ == 0x03:	self.comd.decode(self.data)
		elif self.typ == 0x04:	self.para.decode(self.data)

	def encode(self):
		if self.typ == 0x01:	self.data = self.sens.encode()
		elif self.typ == 0x02:	self.data = self.stat.encode()
		elif self.typ == 0x03:	self.data = self.comd.encode()
		elif self.typ == 0x04:	self.data = self.para.encode()

		return pack( '3B', self.ver, self.ack, self.typ ) + self.data









