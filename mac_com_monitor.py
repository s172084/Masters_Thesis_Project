#!/usr/bin/env python3

import threading
import time
import serial


class ComMonitorThread(threading.Thread):
    """ A thread for monitoring a COM port. The COM port is 
        opened when the thread is started.
    
        data_q:
            Queue for received data. Items in the queue are
            (data, timestamp) pairs, where data is a binary 
            string representing the received data, and timestamp
            is the time elapsed from the thread's start (in 
            seconds).
        
        error_q:
            Queue for error messages. In particular, if the 
            serial port fails to open for some reason, an error
            is placed into this queue.
        
        port:
            The COM port to open. Must be recognized by the 
            system.
        
        port_baud/stopbits/parity: 
            Serial communication parameters
        
        port_timeout:
            The timeout used for reading the COM port. If this
            value is low, the thread will return data in finer
            grained chunks, with more accurate timestamps, but
            it will also consume more CPU.
    """
    
    def __init__(   self, 
                    data_q, error_q, 
                    port_num,
                    port_baud,
                    port_stopbits=serial.STOPBITS_ONE,
                    port_parity=serial.PARITY_NONE,
                    port_timeout=1.0):
        threading.Thread.__init__(self)
        
        self.serial_port = None
        self.serial_arg = dict( port=port_num,
                                baudrate=port_baud,
                                stopbits=port_stopbits,
                                parity=port_parity,
                                timeout=port_timeout)
        
        self.data_q = data_q
        self.error_q = error_q
        
        self.alive = threading.Event()
        self.alive.set()
        
        
        self.wait_for_ack = False
        
        self.index = 0 
        self.scanning = False
        self.data=b''
        
        
    def run(self):
        try:
            if self.serial_port: 
                self.serial_port.close()
            self.serial_port = serial.Serial(**self.serial_arg)
        except serial.SerialException as e:
            self.error_q.put(str(e))
            return
        
        # Restart the clock
        time.process_time()
        
        while self.alive.isSet():
            
            try:
                in_data = [self.serial_port.read(1)]
                in_data.append(self.serial_port.read(self.serial_port.inWaiting()))
                self.data += b''.join(in_data)
                time.sleep(0.1)
            except serial.SerialException as e:
                print('Serial Exception')
                self.error_q.put(str(e))
                self.alive.clear()
                break
            
            if len(self.data):
                data = self.data.split(b'\r\n')
                
                if(len(data)<2):
                    continue
                
                self.data = data[-1] #return last item
                data = data[:-1]
                
                #timestamp = time.process_time()
                for item in data:
                    
                    item = item.strip().split(b' ')
                    if(len(item)==1):
                        item = item[0]
                        #look for scan start symbol
                        
                        try:
                            if(item.find(b'a')>=0):
                                self.scanning = True
                                self.index = 0
                            else:
                                self.scanning = False 
                                self.data_q.put((int(item)))
                        except ValueError as e:
                            print(e) 
                            pass
                        except:
                            print('unknown Error')
                            pass
                            
                    elif (len(item)==256):
                        if self.scanning==False:
                            self.scanning = True
                            self.index = 0
                        self.data_q.put((self.index, [int(i) for i in item]))
                        
                        if(self.index<255):
                            self.index += 1
                        else:
                            self.index = 0
                            
                    else:
                        print('Invalid frame size %i'%len(item))
                        
                        
        # clean up
        if self.serial_port:
            print('com_monitor close serial and exit')
            self.serial_port.close()
            
    def startScan(self, x=0, y=0, speed=2000, gap=1):
        self.send_cmd('p%i'%(speed,))
        self.send_cmd('x%i'%(x,))
        self.send_cmd('y%i'%(y,))
        self.send_cmd('g%i'%(gap,))
        self.send_cmd('u')
        
        self.wait_for_index_reset = True
        
    def stopScan(self):
        #print('StopScan')
        self.send_cmd('e')
        self.scanning = False
        
    def scanSpeed(self,val):        
        self.send_cmd('p%i'%(val,))
        
    def send_cmd(self, cmd_str):
        self.serial_port.write(bytearray(cmd_str.encode('utf-8') + b'\n'))
        
    def send_serial(self, data):
        """Send data to the serial port"""
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(data.encode())
            return True
        return False
    

        
    def join(self, timeout=None):
        print('com_monitor join')
        self.alive.clear()
        threading.Thread.join(self, timeout)