import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "lib"))
import serial
import serial.tools.list_ports
import re
import json
import binascii

def createAndOpen(filename, mode):
	if not os.path.exists(os.path.dirname(filename)):
		os.makedirs(os.path.dirname(filename), 0777)
	return open(filename, mode)

def toHex(s):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0'+hv
        lst.append(hv)
    
    return reduce(lambda x,y:x+y, lst)

class Smartjs(object):
	"""docstring for Smartjs"""
	def __init__(self, arg):
		super(Smartjs, self).__init__()
		self.serial_params = { 'port':'', 'baudrate':115200}
		self.serial = serial.Serial()

	def connect(self):
		self.serial.port = self.serial_params['port']
		self.serial.baudrate = self.serial_params['baudrate']
		self.serial.timeout = .1
		self.serial.open()
		self.sendAndRecieve('var readFile = function(file){var fh = File.open(file);var text;if(fh != null){text = fh.readAll();fh.close();};return text;}')
		return 1

	def close(self):
		if self.serial.isOpen():
			self.serial.close()
		pass

	def readline(self):
		resp = self.serial.readline()
		resp = resp.strip("\n")
		return resp.strip("\r")

	def sendAndRecieve(self, cmd):
		_cmd = cmd+"\n"
		print "CMD:"+cmd
		self.serial.write(_cmd.encode('utf-8'))
		answer = ''
		resp = self.readline()
		if resp == cmd:
			resp = ''
		while not re.match('^smartjs (?:\d+)\/(\d+)\$', resp):
			if re.match('^set_errno', resp):
				print "ERROR : "+resp
			else:
				answer = answer + resp
			resp = self.readline()
		answer = answer.replace("\\n", '\n')
		answer = answer.replace("\\t", '\t')
		answer = answer.replace("\\\"", '"')
		print "ANSW:"+answer
		return answer

	def list_files(self):
		if not self.serial.isOpen():
			self.connect()

		resp = self.sendAndRecieve("File.list('/')")
		files = json.loads(resp)
		def fstruct(fname):
			return {'name': fname.decode('utf-8').encode('ascii')}
		files = map(fstruct, files)
		self.close()
		return files

	def createFile(self, file):
		if not self.serial.isOpen():
			self.connect()
		self.sendAndRecieve('var uf = File.open("'+file['name']+'", "w");')
		self.sendAndRecieve('uf.write("'+file['name']+'");')
		self.sendAndRecieve('uf.close();')
		return 1

	def downloadFile(self, file, file_path):
		if not self.serial.isOpen():
			self.connect()
		local = createAndOpen(file_path, 'w')
		text = self.sendAndRecieve('readFile("'+file['name']+'")')
		text = text.strip('"')
		local.write(text)
		local.close()
		self.close()
		return 1

	def uploadFile(self, file, path):
		fh = open(path)
		print "UPLOADING "+path
		line = fh.read(32)
		if not self.serial.isOpen():
			self.connect()
		self.sendAndRecieve('var uf = File.open("'+file['name']+'", "w");')
		while not line == '':
			bytes = line
			i = len(bytes)
			print bytes
			chunk = ''
			while i>0:
				chunk += '\\x'+toHex(bytes[len(bytes)-i:len(bytes)-i+1])
				i-=1
			print chunk
			self.sendAndRecieve('uf.write("'+chunk+'");')
			line = fh.read(32)
		self.sendAndRecieve('uf.close();')
		self.close()
		return 1

	def list_ports(self):
		iterator = serial.tools.list_ports.comports()
		ports = []
		for port in iterator:
			item = {}
			item['name'], item['description'], item['hw'] = port
			ports.append( item)
		return ports

def new():
	return Smartjs(1)
		