import socket
import select
import time
import threading
from struct import pack, unpack


class looptimer():
	def __init__(self, interval, func, start=False):
		self.interval = interval
		self.func = func
		self.flag = False
		if start: self.start()

	def start(self):
		self.flag = True
		self.__start_loop()

	def stop(self):
		self.flag = False

	def is_alive(self):
		try:	return self.thrd.is_alive()
		except:	return False

	def __start_loop(self):
		if not self.is_alive():
			self.thrd = threading.Thread(target=self.__loop, daemon=True) # daemon means the thread terminates as the main thread exits
			self.thrd.start()

	def __loop(self):
		while self.flag:
			time1 = time.time()
			self.func()
			while time.time()-time1 < self.interval and self.flag: pass


def MySelect(sk_list, operation):
	sks = [ sk for sk in sk_list if sk.fileno() != -1 ]
	if sks != []:
		if operation == 'r': return select.select(sks, [], [], 0) [0] # select() do not accept sockets whose fileno() == -1
		if operation == 'w': return select.select([], sks, [], 0) [1] # on Windows select() do not accept all three empty list
	return []


# note: socket is like a file on hardware, I/O is about the memory:
# memory read from socket: Input; memory write to socket: output

class Server():
	def __init__(self):
		self.sk0 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sk0.bind(('', 8006))
		self.sk0.listen()

		self.addresses = {self.sk0: socket.gethostbyname(socket.gethostname())}
		self.I_sockets = {self.sk0: []}	# byte packages received
		self.O_sockets = {}	# byte packages ready to be sent
		self.I_streams = {}	# raw byte stream received
		self.last_time = {}	# time of the last receive

		self.heartbeat = b'heartbeat'
		self.framehead = b'framehead'

		print('Server', self.addresses[self.sk0], 'initiated')

		self.timer = looptimer(1, self.detect, start=True)

##### receive and send (main functional methods) #####
	def recv(self):
		self.read()
		for sk in self.I_sockets.keys():
			while self.I_sockets[sk]: datastring = self.I_sockets[sk].pop(0)
		try:	return datastring	# for efficiency, only the last frame is returned, others are dumped
		except:	return None

	def send(self, datastring):
		for sk in self.O_sockets.keys(): self.O_sockets[sk].append(datastring)
		self.write()

	def interact(self, func=None):
		self.read()
		for sk in self.I_sockets.keys():
			while self.I_sockets[sk]:
				datastring = self.I_sockets[sk].pop(0)
				ans = self.testfunc(datastring) if not func else func(datastring)
				if ans: self.O_sockets[sk].append(ans)
		self.write()
######################################################

##### read and write #####
	def read(self):
		for sk in MySelect(self.I_sockets.keys(), 'r'):	# select out sockets that are ready for reading
			if sk == self.sk0: self.add( *sk.accept() )	# new client connected
			else:
				try: datastring = sk.recv(1024)			# read message from old connections
				except Exception as ex: self.remove(sk, ex)
				else:
					if datastring:
						self.I_streams[sk] += datastring
						self.decode(sk)

	def write(self):
		for sk in MySelect(self.O_sockets.keys(), 'w'):  # select out sockets that are ready for writing, wait at most 1 second
			try:
				while self.O_sockets[sk]: sk.sendall( self.encode( self.O_sockets[sk].pop(0) ) )
			except Exception as ex:	self.remove(sk, ex)
##########################

##### decode and encode #####
	def decode(self, sk):
		self.last_time[sk] = time.time()  # decode is only called when stream is updated, meaning receive succeeded

		stream = self.I_streams[sk]

		while True:											# see self.encode() for the structure of the frame
			len_st = len(stream)
			idx_hd = len_st if (self.framehead not in stream) else stream.index(self.framehead)
			idx_ht = len_st if (self.heartbeat not in stream) else stream.index(self.heartbeat)
			idx = min(idx_hd, idx_ht)

			if idx == len_st: break							# neither in the stream, do nothing and break. (wait for the next receive in case framehead is truncated)
			elif idx == idx_ht:	idx += len(self.heartbeat)	# heart in the stream, skip and continue
			elif idx == idx_hd:								# head in the stream, read the package
				i = idx + len(self.framehead) + 4
				if len_st < i: break
				len_dt, = unpack( 'I', stream[i-4 : i] )	# the length of the package, maximum 2^32-1 bytes
				if len_st < len_dt + i + 8: break			# the whole package cannot fit in the stream, do nothing and continue (wait for the next receive)
				
				datastring = stream[i : i+len_dt]			# the whole package and the tail checksum are included in the stream, read the package
				i += len_dt
				checksum, = unpack( 'Q', stream[i : i+8] )	# 'Q' stands for long long unsigned integer
				if checksum != sum(datastring):	idx += len(self.framehead)	# check failed, skip the head and continue
				else:										# check succeeded, add the package to the package list
					self.I_sockets[sk].append(datastring)
					idx = i + 8

			stream = stream[idx:]							# dump the part that has already been processed. note: if idx>len(stream), stream become empty

		self.I_streams[sk] = stream

	def encode(self, datastring):
		if datastring == self.heartbeat: return datastring
		else: return self.framehead + pack('I', len(datastring)) + datastring + pack('Q', sum(datastring))
#############################

##### add and remove #####
	def add(self, sk, address):
		self.I_sockets[sk] = []
		self.O_sockets[sk] = []
		self.I_streams[sk] = b''
		self.addresses[sk] = address
		self.last_time[sk] = time.time()
		print('\nConnected by', address, ', connection number', len(self.I_sockets) - 1)

	def remove(self, sk, ex=None):
		try:	sk.close()
		except:	pass
		if ex:	print('\nException =', ex)
		if sk in self.I_sockets.keys():	self.I_sockets.pop(sk)
		if sk in self.O_sockets.keys():	self.O_sockets.pop(sk)
		if sk in self.I_streams.keys(): self.I_streams.pop(sk)
		if sk in self.addresses.keys():	print(self.addresses.pop(sk), 'removed, connection number', len(self.I_sockets)-1)
		if sk in self.last_time.keys(): self.last_time.pop(sk)
##########################

##### others #####
	def detect(self, timeout=5):
		self.read()
		timeout_list = [ sk for sk in self.last_time.keys() if (time.time() - self.last_time[sk] > timeout) ]
		for sk in timeout_list: self.remove(sk, ex='Disconnected')
		for sk in self.O_sockets.keys(): self.O_sockets[sk].append(self.heartbeat)
		self.write()

	def get_connection_state(self):
		return len(self.I_sockets) > 1

	def testfunc(self, datastring):
		return datastring
##################







class Client():

	def __init__(self, serverIP='', start=False):
		self.serverIP = serverIP
		self.flag = False
		self.address = socket.gethostbyname(socket.gethostname())
		self.heartbeat = b'heartbeat'
		self.framehead = b'framehead'
		self.timer = looptimer(1, self.detect)
		print("Client", self.address, "initiated\n")

		if start: self.open()

##### open, close and reconnection #####
	def open(self):
		if not self.flag:
			self.flag = True
			if not (hasattr(self, 'opening') and self.opening.is_alive()):
				self.opening = threading.Thread(target=self.open_operation)
				self.opening.start() # open the socket in a separate thread to avoid blocking
	def open_operation(self):
		while self.flag and not self.is_opened(): # if self.close() called during opening, open abort
			try: self.sk = socket.create_connection((self.serverIP, 8006), timeout=1)
			except:
				print("Connection failed, waiting for reconnection...")
				time.sleep(1)

		if self.flag:
			self.I_socket = []
			self.O_socket = []
			self.I_stream = b''
			self.last_time = time.time()
			self.timer.start() # self.detect() runs immediately as timer starts, make sure all dependencies are initiated before
			print("Server", self.serverIP, "connected!\n")
		else:
			if self.is_opened(): self.sk.close() # in case self.close() called during create_connection()

	def close(self):
		if self.flag:
			self.flag = False
			self.timer.stop()
			if self.is_opened(): self.sk.close()

	def restart(self, ex=None):
		self.close()
		if ex: print("\nException =", ex)
		self.open()
#######################################

##### receive and send (main functional methods) #####
	def recv(self):
		self.read()
		while self.I_socket: datastring = self.I_socket.pop(0)
		try:	return datastring	# for efficiency, only the last frame is returned, others are dumped
		except:	return None

	def send(self, datastring):
		if self.is_opened(): self.O_socket.append(datastring)
		self.write()
		
	def interact(self, func=None):
		self.read()
		while self.I_socket:
			datastring = self.I_socket.pop(0)
			ans = self.testfunc(datastring) if not func else func(datastring)
			if ans: self.O_socket.append(ans)
		self.write()
######################################################

##### read and write #####
	def read(self):
		for sk in MySelect([self.sk], 'r'):
			try: datastring = sk.recv(1024)
			except Exception as ex: pass
			else:
				if datastring:
					self.I_stream += datastring
					self.decode()

	def write(self):
		for sk in MySelect([self.sk], 'w'):
			try:
				while self.O_socket: sk.sendall(self.encode(self.O_socket.pop(0)))
			except Exception as ex: pass
##########################

##### decode and encode #####
	def decode(self):
		self.last_time = time.time()  # decode is only called when stream is updated, meaning receive succeeded

		stream = self.I_stream

		while True:
			len_st = len(stream)
			idx_hd = len_st if (self.framehead not in stream) else stream.index(self.framehead)
			idx_ht = len_st if (self.heartbeat not in stream) else stream.index(self.heartbeat)
			idx = min(idx_hd, idx_ht)

			if idx == len_st: break						# neither in the stream, do nothing and break. (wait for the next receive in case framehead is truncated)
			elif idx == idx_ht:
				self.O_socket.append(self.heartbeat)  	# heart in the stream, echo back. note: this is different from server
				idx += len(self.heartbeat)
			elif idx == idx_hd:							# head in the stream, read the package
				i = idx + len(self.framehead) + 4
				if len_st < i: break
				len_dt, = unpack( 'I', stream[i-4: i] )	# the length of the package, maximum 2^32-1 bytes
				if len_st < len_dt + i + 8:	break		# the whole package cannot fit in the stream, do nothing and continue (wait for the next receive)

				datastring = stream[i: i+len_dt]		# the whole package and the tail checksum are included in the stream, read the package
				i += len_dt
				checksum, = unpack( 'Q', stream[i: i+8] )
				if checksum != sum(datastring):			# check failed, skip the head and continue
					idx += len(self.framehead)
				else:									# check succeeded, add the package to the package list
					self.I_socket.append(datastring)
					idx = i + 8

			stream = stream[idx:]  						# dump the part that has already been processed. note: if idx>len(stream), stream become empty

		self.I_stream = stream

	def encode(self, datastring):
		if datastring == self.heartbeat: return datastring
		else: return self.framehead + pack('I', len(datastring)) + datastring + pack('Q', sum(datastring))
#############################

##### others #####
	def detect(self, timeout=3):
		self.read()
		if time.time() - self.last_time > timeout: self.restart(ex='Disconnected')
		if self.heartbeat in self.O_socket:	self.write()

	def is_opened(self):
		try:	return self.sk.fileno() != -1
		except:	return False

	def get_connection_state(self):
		return self.flag and self.is_opened()

	def testfunc(self, datastring):
		print(datastring.decode())
		return b''
##################





class test():
	def __init__(self, serverIP=''):
		if serverIP == '':
			self.srv = Server()
			self.servertest()
		else:
			self.clt = Client(serverIP, True)
			self.clienttest()

	def servertest(self):
		while True:
			self.srv.interact()
			time.sleep(0.2)

	def clienttest(self):
		cnt = 10
		while cnt > 0:
			data_str = 'test message %i from client' % cnt
			self.clt.send(data_str.encode())
			time.sleep(cnt/4.0)
			self.clt.interact()

			cnt -= 1

		self.clt.close()
		print('I am closed')
		time.sleep(10)

		print('I am opening')
		self.clt.open()


if __name__ == '__main__':
	
	datastring = pack( '3B', 0x01, 0x01, 0x01 ) + b'test'

	s = Server()
	while True:
		s.send(datastring)
		time.sleep(0.02)
		s.interact()



