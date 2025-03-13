#!/usr/bin/env python3

import serial
import glob
import serial.tools.list_ports

def enumerate_serial_ports():
    """
    Return a list of serial port names available on macOS
    """
    # This will find all available serial ports on macOS
    #ports = glob.glob('/dev/tty.*') + glob.glob('/dev/cu.*')
    #return ports
    return [port.device for port in serial.tools.list_ports.comports()]

def full_port_name(portname):
    """
    On macOS, port names are already fully specified
    """
    return portname

def list_ports_info():
    """
    Returns detailed information about available ports
    """
    try:
        import serial.tools.list_ports
        return list(serial.tools.list_ports.comports())
    except:
        return []

