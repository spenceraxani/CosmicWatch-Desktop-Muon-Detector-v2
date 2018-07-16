import serial 
import time
import glob
import sys
import os
import os.path
import signal
from datetime import datetime
from multiprocessing import Process

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web
import socket
import multiprocessing
import math
import random
import thread
import serial 

'''
This is a Websocket server that forwards signals from the detector to any client connected.
It requires Tornado python library to work properly.
Please run `pip install tornado` with python of version 2.7.9 or greater to install tornado.
Run it with `python detector-server.py`
Written by Pawel Przewlocki (pawel.przewlocki@ncbj.gov.pl).
Based on http://fabacademy.org/archives/2015/doc/WebSocketConsole.html
''' 
clients = [] ##list of clients connected
queue = multiprocessing.Queue() #queue for events forwarded from the device

class DataCollectionProcess(multiprocessing.Process):
    def __init__(self, queue):
        #multiprocessing.Process.__init__(self)
        self.queue = queue
        self.comport = serial.Serial(port_name) # open the COM Port
        self.comport.baudrate = 9600          # set Baud rate
        self.comport.bytesize = 8             # Number of data bits = 8
        self.comport.parity   = 'N'           # No parity
        self.comport.stopbits = 1 

    def close(self):
        self.comport.close()
        
    def nextTime(self, rate):
        return -math.log(1.0 - random.random()) / rate

def RUN(bg):
    print 'Running...'
    while True:
        data = bg.comport.readline()
        bg.queue.put(str(datetime.now())+" "+data)
    
class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__ (self, application, request, **kwargs):
        super(WSHandler, self).__init__(application, request, **kwargs)
        self.sending = False

    def open(self):
        print 'New connection opened from ' + self.request.remote_ip
        clients.append(self)
        print '%d clients connected' % len(clients)
      
    def on_message(self, message):
        print 'message received:  %s' % message
        if message == 'StartData':
            self.sending = True
        if message == 'StopData':
            self.sending = False
 
    def on_close(self):
        self.sending = False
        clients.remove(self)
        print 'Connection closed from ' + self.request.remote_ip
        print '%d clients connected' % len(clients)
 
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
        ComPort.close()     
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

#If the Arduino is not recognized by your computer, make sure you have
#   installed the drivers for the Arduino.
print('\n             Welcome to:   ')
print('CosmicWatch: The Desktop Muon Detector\n')

port_list = serial_ports()

print('Available serial ports:\n')
for i in range(len(port_list)):
    print('['+str(i+1)+'] ' + str(port_list[i]))
print('[h] help\n')

ArduinoPort = raw_input("Select Arduino Port: ")
port_name = str(port_list[int(ArduinoPort)-1])

if ArduinoPort == 'h':
    print_help1()
    sys.exit()

print("The selected port is: " + port_name+'\n')

print("What would you like to do:")
print("[1] Record data on the computer")
print("[2] Copy data files from SD card to your computer")
print("[3] Remove files from SD card")
print("[4] Connect to server: www.cosmicwatch.lns.mit.edu")
print("[h] Help")

mode = int(raw_input("\nSelect operation: "))

if mode == 'h':
    print_help2()
    sys.exit()

if mode == 1:
    fname = raw_input("Enter file name (eg. /Users/HAL9000/Desktop/test.txt):")
    if fname == '':
        fname = 'data.txt'
    print("\nTaking data ...")
    print("Press ctl+c to terminate process")
    signal.signal(signal.SIGINT, signal_handler)
    ComPort = serial.Serial(port_name) # open the COM Port
    ComPort.baudrate = 9600          # set Baud rate
    ComPort.bytesize = 8             # Number of data bits = 8
    ComPort.parity   = 'N'           # No parity
    ComPort.stopbits = 1 
    time.sleep(1)
    ComPort.write('write')   
    file = open(fname, "w",0)
    counter = 0
    header1 = ComPort.readline()    # Wait and read data 
    header2 = ComPort.readline()    # Wait and read data 
    header3 = ComPort.readline()     # Wait and read data 
    header4 = ComPort.readline()     # Wait and read data 
    header5 = ComPort.readline()     # Wait and read data 
    file.write(header1)
    file.write(header2)
    file.write(header3)
    file.write(header4)
    file.write(header5)
    detector_name = ComPort.readline()    # Wait and read data 
    file.write("Device ID: "+str(detector_name))

    while True:
        data = ComPort.readline()    # Wait and read data 
        file.write(str(datetime.now())+" "+data)
        ComPort.write('got-it') 
    ComPort.close()     
    file.close()  

if mode == 2:
    print("Opening files on SD card... ")
    signal.signal(signal.SIGINT, signal_handler)
    ComPort = serial.Serial(port_name) # open the COM Port
    ComPort.baudrate = 9600            # set Baud rate
    ComPort.bytesize = 8               # Number of data bits = 8
    ComPort.parity   = 'N'             # No parity
    ComPort.stopbits = 1 

    if ComPort.readline().strip() == 'CosmicWatchDetector':
        time.sleep(1)
        detector_name = ComPort.readline()
        dir_path = os.path.dirname(os.path.realpath(__file__))+ '/SDFiles'
        if not os.path.exists(dir_path):
                os.makedirs(dir_path)
        ComPort.write("read") 
        counter = 0
        while True:
            data = ComPort.readline()    # Wait and read data 
            if 'Done' in data:
                ComPort.close() 
                sys.exit() 
            elif 'opening:' in data:
                fname = dir_path + '/' + data.split(' ')[-1].split('.txt')[0]+'.txt'
                
                print("Saving to: "+ fname)
                file = open(fname, "w",0)
                counter = 0
                #file.write("###################################################################################\n")
                #file.write("### CosmicWatch: The Desktop Muon Detector \n")
                #file.write("### Questions? saxani@mit.edu \n")
                #file.write("### Event_id Ardn_time[ms] ADC_value[0-1023] SiPM[mV] Deadtime[ms] Temperature[C]\n")
                #file.write("###################################################################################\n")
                #file.write("Device ID: "+str(detector_name))

            elif 'EOF' in data:
                file.close() 
            
            else:
                file.write(data)
                counter +=1
   


    else:
	print('You are trying to read from the SD card. Does the Arduino have the SD card code on it?')
        print('Your detector may not have an SD card inserted')
        sys.exit()


if mode == 3:
    print("\nAre you sure that you want to remove all files from SD card?")
    ans = raw_input("Type y or n: ")
    if ans == 'y' or ans == 'yes' or ans == 'Y' or ans == 'YES':
        signal.signal(signal.SIGINT, signal_handler)
        ComPort = serial.Serial(port_name) # open the COM Port
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
            print('Error, check the following:')
            print('- Is there an SD card inserted?')
            print('- Make sure you have the sd_card.ino code uploaded to the Arduino.')
            sys.exit()

    else:
        print("Exiting program")
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
    print 'CosmicWatch detector server started at %s:%d' % (myIP, port)
    print 'You can now connect to your device using http://cosmicwatch.lns.mit.edu/'
    mainLoop = tornado.ioloop.IOLoop.instance()
    #in the main loop fire queue check each 100ms
    scheduler = tornado.ioloop.PeriodicCallback(checkQueue, 100, io_loop = mainLoop)
    scheduler.start()
    #start the loop
    mainLoop.start()


def print_help1():
    print('\n===================== help =======================')
    print('This code looks through the serial ports. ')
    print('You must select which one is the Arduino.\n')
    print('If you have problems, check the following:')
    print('1. Is your Arduino connected to the serial USB port?\n')
    print('2. Check that you have the correct drivers installed:\n')
    print('\tMacOS: CH340g driver (try: https://github.com/adrianmihalko/ch340g-ch34g-ch34x-mac-os-x-driver)')
    print('\tWindows: no dirver needed')
    print('\tLinux: no driver needed')


def print_help2():
    print('\n===================== help =======================')
    print('With this code you can record data from you connected')
    print('Desktop Muon Detector to the computer (option 1), or you can')
    print('connect to the website to plot data in real-time (option 2).')

