import time
import glob
import sys
import os
import os.path
import signal
from datetime import datetime
from multiprocessing import Process

#import numpy as np
import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import multiprocessing
import math
import random
import _thread
import serial 

'''
This is a Websocket server that forwards signals from the detector to any client connected.
It requires Tornado python library to work properly.
Please run `pip install tornado` with python of version 2.7.9 or greater to install tornado.
Run it with `python detector-server.py`
Written by Pawel Przewlocki (pawel.przewlocki@ncbj.gov.pl).
Based on http://fabacademy.org/archives/2015/doc/WebSocketConsole.html
'''

global ComPort
ComPort = None
global file
file = None

def print_help1():
    print('\n===================== HELP =======================')
    print('This code looks through the serial ports. ')
    print('You can select multiple ports with by separating the port number with commas.')
    print('You must select which port contains the Arduino.\n')
    print('If you have problems, check the following:')
    print('1. Is your Arduino connected to the serial USB port?\n')
    print('2. Check that you have the correct drivers installed:\n')
    print('\tMacOS: CH340g driver (try: https://github.com/adrianmihalko/ch340g-ch34g-ch34x-mac-os-x-driver)')
    print('\tWindows: no dirver needed')
    print('\tLinux: no driver needed')


clients = [] ## list of clients connected
queue = multiprocessing.Queue() #queue for events forwarded from the device

class DataCollectionProcess(multiprocessing.Process):
    def __init__(self, queue):
        #multiprocessing.Process.__init__(self)
        self.queue = queue
        self.comport = serial.Serial(port_name_list[0]) # open the COM Port
        self.comport.baudrate = 9600          # set Baud rate
        self.comport.bytesize = 8             # Number of data bits = 8
        self.comport.parity   = 'N'           # No parity
        self.comport.stopbits = 1 

    def close(self):
        self.comport.close()
        
    def nextTime(self, rate):
        return -math.log(1.0 - random.random()) / rate

def RUN(bg):
    print('Running...')
    while True:
        data = bg.comport.readline()
        bg.queue.put(str(datetime.now())+" "+data)
    
class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__ (self, application, request, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.sending = False

    def open(self):
        print('New connection opened from ' + self.request.remote_ip)
        clients.append(self)
        print('%d clients connected' % len(clients))
      
    def on_message(self, message):
        print('message received:  %s' % message)
        if message == 'StartData':
            self.sending = True
        if message == 'StopData':
            self.sending = False
 
    def on_close(self):
        self.sending = False
        clients.remove(self)
        print('Connection closed from ' + self.request.remote_ip)
        print('%d clients connected' % len(clients))
 
    def check_origin(self, origin):
        return True

def checkQueue():
    while not queue.empty():
        message = queue.get()
        ##sys.stdout.write('#')
        for client in clients:
            if client.sending:
                client.write_message(message)
 

def signal_handler(signal, frame):
	print('You pressed Ctrl+C!')
	if ComPort:
		ComPort.close()
	if file:
		file.close()
	sys.exit(0)

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
        sys.exit(0)
    result = []
    for port in ports:
        try: 
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

#If the Arduino is not recognized by your MAC, make sure you have
#   installed the drivers for the Arduino (CH340g driver). Windows and Linux don't need it.

print('\n             Welcome to:   ')
print('CosmicWatch: The Desktop Muon Detector\n')

print("What would you like to do:")
print("[1] Record data on the computer")
print("[2] Copy data files from SD card to your computer")
print("[3] Remove files from SD card")
print("[4] Connect to server: www.cosmicwatch.lns.mit.edu")
print("[h] Help")

mode = str(input("\nSelected operation: "))

if mode == 'h':
    print_help1()
    sys.exit()

else:
	mode = int(mode)
	if mode not in [1,2,3,4]:
		print('-- Error --')
		print('Invalid selection')
		print('Exiting...')
		sys.exit()

port_list = serial_ports()

print('Available serial ports:')
for i in range(len(port_list)):
    print('['+str(i+1)+'] ' + str(port_list[i]))
print('[h] help\n')

ArduinoPort = input("Selected Arduino port: ")

ArduinoPort = ArduinoPort.split(',')
nDetectors = len(ArduinoPort)

if mode in [2,3,4]:
	if len(ArduinoPort) > 1:
		print('--- Error ---')
		print('You selected multiple detectors.')
		print('This options is only compatible when recording to the computer.')
		print('Exiting...')
		sys.exit()

port_name_list = []

for i in range(len(ArduinoPort)):
	port_name_list.append(str(port_list[int(ArduinoPort[i])-1]))

if ArduinoPort == 'h':
    print_help1()
    sys.exit()

print("The selected port(s) is(are): ")
for i in range(nDetectors):	 
	print('\t['+str(ArduinoPort[i])+']' +port_name_list[i])


if mode == 1:
	cwd = os.getcwd()
	fname = input("Enter file name (default: "+cwd+"/CW_data.txt):")

	detector_name_list = []
	
	if fname == '':
	    fname = cwd+"/CW_data.txt"

	print('Saving data to: '+fname)

	#ComPort_list = np.ones(nDetectors)
	for i in range(nDetectors):
		signal.signal(signal.SIGINT, signal_handler)
		globals()['Det%s' % str(i)] = serial.Serial(str(port_name_list[i]))
		globals()['Det%s' % str(i)].baudrate = 9600    
		globals()['Det%s' % str(i)].bytesize = 8             # Number of data bits = 8
		globals()['Det%s' % str(i)].parity   = 'N'           # No parity
		globals()['Det%s' % str(i)].stopbits = 1 

		time.sleep(1)
		#globals()['Det%s' % str(i)].write('write')  

		counter = 0

		header1 = globals()['Det%s' % str(i)].readline()     # Wait and read data
		if 'SD initialization failed' in header1.decode():
			print('...SDCard.ino detected.')
			print('...SDcard initialization failed.')
			# This happens if the SDCard.ino is uploaded but it doesn't see an sdcard.
			header1a = globals()['Det%s' % str(i)].readline()
			header1 = globals()['Det%s' % str(i)].readline()
		if 'CosmicWatchDetector' in header1.decode():
			print('...SDCard.ino code detected.')
			print('...SDcard intialized correctly.')
			# This happens if the SDCar.ino is uploaded and it sees an sdcard.
			header1a = globals()['Det%s' % str(i)].readline()
			globals()['Det%s' % str(i)].write('write') 
			header1b = globals()['Det%s' % str(i)].readline()
			header1 = globals()['Det%s' % str(i)].readline()
			#header1 = globals()['Det%s' % str(i)].readline()
		header2 = globals()['Det%s' % str(i)].readline()     # Wait and read data 
		header3 = globals()['Det%s' % str(i)].readline()     # Wait and read data 
		header4 = globals()['Det%s' % str(i)].readline()     # Wait and read data 
		header5 = globals()['Det%s' % str(i)].readline()     # Wait and read data 

		det_name = globals()['Det%s' % str(i)].readline().decode().strip()
		#print(det_name)
		if 'Device ID: ' in det_name:
			det_name = det_name.split('Device ID: ')[-1]
		detector_name_list.append(det_name)    # Wait and read data 


	file = open(fname, "w")
	file.write(header1.decode())
	file.write(header2.decode())
	file.write(header3.decode())
	file.write(header4.decode())
	file.write(header5.decode())

	string_of_names = ''
	print("\n-- Detector Names --")
	#print(detector_name_list)
	for i in range(len(detector_name_list)):
		print(detector_name_list[i])
		if '\xff' in detector_name_list[i] or '?' in detector_name_list[i] :
			print('--- Error ---')
			print('You should name your CosmicWatch Detector first.')
			print('Simply change the DetName variable in the Naming.ino script,')
			print('and upload the code to your Arduino.')
			print('Exiting ...')

	print("\nTaking data ...")
	print("Press ctl+c to terminate process")

	if nDetectors>1:
		for i in range(nDetectors):
			string_of_names += detector_name_list[i] +', '
	else:
		string_of_names+=detector_name_list[0]

	#print(string_of_names)
	file.write('Device ID(s): '+string_of_names)
	file.write('\n')
	#detector_name = ComPort.readline()    # Wait and read data 
	#file.write("Device ID: "+str(detector_name))

	while True:
		for i in range(nDetectors):
			if globals()['Det%s' % str(i)].inWaiting():
				#data = globals()['Det%s' % str(i)].readline().replace(
				# '\r\n','')    # Wait and read data
				data = globals()['Det%s' % str(i)].readline().decode(
					).strip()	# Wait and read data
				file.write(str(datetime.now())+" "+data+" "+detector_name_list[i]+'\n')
				globals()['Det%s' % str(i)].write(str.encode('got-it'))

	for i in range(nDetectors):
		globals()['Det%s' % str(i)].close()     
	file.close()  

if mode == 2:
	
	cwd = os.getcwd()
	dir_path = input("\nEnter location to save SD data (default: "+cwd+"/SDFiles):")
	if dir_path == '':
		dir_path = cwd+"/SDFiles"
	
	if not os.path.exists(dir_path):
		os.makedirs(dir_path)


	signal.signal(signal.SIGINT, signal_handler)
	ComPort = serial.Serial(port_name_list[0]) # open the COM Port
	ComPort.baudrate = 9600            # set Baud rate
	ComPort.bytesize = 8               # Number of data bits = 8
	ComPort.parity   = 'N'             # No parity
	ComPort.stopbits = 1 

	if ComPort.readline().strip() == 'CosmicWatchDetector':
		time.sleep(1)
		detector_name = ComPort.readline()
		
		print('\n-- Detector Name --')
		print(detector_name)

		ComPort.write("read") 
		counter = 0


		while True:
			data = ComPort.readline()    # Wait and read data 
			#print(data)
			if 'Done' in data:
			    ComPort.close() 
			    sys.exit() 
			elif 'opening:' in data:
			    fname = dir_path + '/' + data.split(' ')[-1].split('.txt')[0]+'.txt'
			    
			    print("Saving to: "+ fname)
			    file = open(fname, "w",0)
			    counter = 0


			elif 'EOF' in data:
			    file.close() 

			else:
			    file.write(data)
			    counter +=1
   
	else:
		print('--- Error ---')
		print('You are trying to read from the SD card.')
		print('Have you uploaded SDCard.ino to the Arduino?')
		print('Is there a microSD card inserted into the detector?')
		print('Exiting ...')
		sys.exit()

if mode == 3:
    print("\nAre you sure that you want to remove all files from SD card?")
    ans = input("Type y or n: ")
    if ans == 'y' or ans == 'yes' or ans == 'Y' or ans == 'YES':
        signal.signal(signal.SIGINT, signal_handler)
        ComPort = serial.Serial(port_name_list[0]) # open the COM Port
        ComPort.baudrate = 9600          # set Baud rate
        ComPort.bytesize = 8             # Number of data bits = 8
        ComPort.parity   = 'N'           # No parity
        ComPort.stopbits = 1 

        if ComPort.readline().strip() == 'CosmicWatchDetector':
            time.sleep(1)
            ComPort.write("remove")   
            while True:
                data = ComPort.readline()    # Wait and read data 
                print(data)
                if data == 'Done...\r\n':
                    print("Finished deleting files.")
                    break
            ComPort.close()     
            sys.exit()

        else:
            print('--- Error ---')
            print('You are trying to remove files from the microSD card.')
            print('Is there an SD card inserted?')
            print('Do you have the correct code on the Arduino? SDCard.ino')
            print('Exiting ...')
            sys.exit()

    else:
        print("Exiting ...")
        sys.exit()

if mode == 4:
    bg = DataCollectionProcess(queue) 
    #bg.daemon = True
    #bg.start()
    thread.start_new_thread(RUN,(bg,)) 
    #p=multiprocessing.Process(target=RUN)
    #p.start()
    #server stuff
    application = tornado.web.Application(
        handlers=[(r'/', WSHandler)]
    )
    http_server = tornado.httpserver.HTTPServer(application)
    port = 9090
    http_server.listen(port)
    myIP = socket.gethostbyname(socket.gethostname())
    print('CosmicWatch detector server started at %s:%d' % (myIP, port))
    print('You can now connect to your device using http://cosmicwatch.lns.mit.edu/')
    mainLoop = tornado.ioloop.IOLoop.instance()
    #in the main loop fire queue check each 100ms
    try:
    	scheduler = tornado.ioloop.PeriodicCallback(checkQueue, 100, io_loop = mainLoop)
    except:
    	# io_loop arguement was removed in version 5.x of Tornado.
    	scheduler = tornado.ioloop.PeriodicCallback(checkQueue, 100)
    scheduler.start()
    #start the loop
    mainLoop.start()



