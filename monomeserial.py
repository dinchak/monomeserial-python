# monomeserial.py for windows 
# author: tom dinchak (dinchak@gmail.com)
# 
# usage:
# download / install python 2.6.5 from http://www.python.org/download
#   direct link: http://www.python.org/ftp/python/2.6.5/python-2.6.5.msi
# download / install pyusb 1.6 from http://bleyer.org/pyusb
#   direct link: http://bleyer.org/pyusb/PyUSB-1.6.win32-py2.6.exe
# run monomeserial.py

import d2xx
import OSC
import threading
import time

# this is the ip / port monomeserial listens on (listen port)
listenAddr = "localhost", 8080

# this is the ip / port monomeserial sends on (host port)
sendAddr = "localhost", 8000

# 0 = off, 1 = on
debugMode = 1

# number of grids
grids = 0

class MonomeThread (threading.Thread):
    def __init__(self, deviceInfo, oscClient):
        self.oscClient = oscClient
        self.deviceInfo = deviceInfo
        self.adcValues = []
        threading.Thread.__init__(self)
    def run(self):
        while 1:
            time.sleep(0.01)
            status = self.deviceInfo['device'].getStatus()
            while status[0] > 0:
                status = self.deviceInfo['device'].getStatus()
                if status[0] == 0:
                    break
                data = self.deviceInfo['device'].read(2)
                b1 = ord(data[0])
                b2 = ord(data[1])
                # handle adc message
                if b1 >> 4 == 14:
                    port = b1 & 0x0F
                    floatVal = float(b2) / 255.0
                    if self.adcValues[port] != floatVal:
                        self.adcValues[port] = floatVal
                        msg = OSC.OSCMessage()
                        if device['tiltmode'] == 1:
                            msg.setAddress(self.deviceInfo['prefix'] + "/tilt")
                            msg.append(self.adcValues[0])
                            msg.append(self.adcValues[1])
                            if debugMode == 1:
                                print msg
                        else:
                            msg.setAddress(self.deviceInfo['prefix'] + "/adc")
                            msg.append(port)
                            msg.append(floatVal)
                            if debugMode == 1:
                                print msg
                        self.oscClient.send(msg)
                    continue
                # handle press messages
                act = b1
                if self.deviceInfo['type'] != "40h":
                    act = 1 - (act >> 4)
                if act == 0 or act == 1:
                    x = b2 >> 4
                    x += self.deviceInfo['offsetX']
                    x = adjustCableX(x, self.deviceInfo);
                    y = b2 & 0x0F
                    y += self.deviceInfo['offsetY']
                    y = adjustCableY(y, self.deviceInfo);
                    if debugMode == 1:
                        print "%s/press %d %d %d" % (self.deviceInfo['prefix'], x, y, act)
                    msg = OSC.OSCMessage()
                    msg.setAddress(self.deviceInfo['prefix'] + "/press")
                    msg.append(x)
                    msg.append(y)
                    msg.append(act)
                    self.oscClient.send(msg)
                elif debugMode == 1:
                    print "unknown message: %d(%s) %d(%s)" % (b1, data[0], b2, data[1])
                    
def getDevicesFromAddress(addr):
    parts = addr.split('/')
    prefix = "/" + parts[1]
    matchingDevices = []
    for deviceInfo in devices:
        if prefix == deviceInfo['prefix']:
            matchingDevices.append(deviceInfo)
    return matchingDevices

def getWidth(type, grids):
    if type == "512":
        return 32
    if type == "128" or type == "256" or grids > 1:
        return 16
    return 8

def getHeight(type, grids):
    if type == "256" or grids > 3:
        return 16
    return 8
    
def adjustCableX(val, device):
    width = getWidth(device['type'], device['grids'])
    if device['cable'] == "right":
        return width - val - 1
    if device['cable'] == "down":
        return width - val - 1
    return val
        
def adjustCableY(val, device):
    height = getHeight(device['type'], device['grids'])
    if device['cable'] == "right":
        return height - val - 1
    if device['cable'] == "up":
        return height - val - 1
    return val

def ledHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    matchingDevices = getDevicesFromAddress(addr)
    for device in matchingDevices:
        width = getWidth(device['type'], device['grids'])
        height = getHeight(device['type'], device['grids'])
        ledX = stuff[0] - device['offsetX']
        ledY = stuff[1] - device['offsetY']
        if ledX < 0 or ledX >= width:
            continue
        if ledY < 0 or ledY >= height:
            continue
        ledX = adjustCableX(ledX, device)
        ledY = adjustCableY(ledY, device)
        ledCmd(device, ledX, ledY, stuff[2])
    return None
    
def ledCmd(device, ledX, ledY, act):
    if device['type'] == "40h":
        b1 = 0x20 + act
    else:
        b1 = (2 + (1 - act)) << 4
    b2 = (ledX << 4) + ledY
    device['device'].write(chr(b1) + chr(b2))

def ledRowHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    matchingDevices = getDevicesFromAddress(addr)
    didDouble = 0
    for i in range(len(stuff)):
        if i == 0:
            row = stuff[i]
            continue
        if didDouble == 1:
            didDouble = 0
            continue
        for device in matchingDevices:
            width = getWidth(device['type'], device['grids'])
	    height = getHeight(device['type'], device['grids'])
            rowStartX = ((i - 1) * 8) - device['offsetX']
            rowStartY = row - device['offsetY']
            if rowStartX < 0 or rowStartX >= width:
                continue
            if rowStartY < 0 or rowStartY >= height:
                continue
            if device['cable'] == "left" or device['cable'] == "right":
                fortyHCmd = 0x70
                seriesCmd = 0x40
                seriesDoubleCmd = 0x60
                deviceRow = adjustCableY(rowStartY, device)
            else:
                fortyHCmd = 0x80
                seriesCmd = 0x50
                seriesDoubleCmd = 0x70
                deviceRow = adjustCableX(rowStartY, device)
            if len(stuff) - i == 1 or device['type'] == "40h":
                if device['type'] == "40h":
                    b1 = fortyHCmd + deviceRow
                else:
                    b1 = seriesCmd + deviceRow
                b2 = stuff[i]
                device['device'].write(chr(b1) + chr(b2))
            else:
                b1 = chr(int(seriesDoubleCmd) + int(deviceRow))
                b2 = chr(stuff[i])
                b3 = chr(stuff[i+1])
                device['device'].write(str(b1) + str(b2) + str(b3))
                didDouble = 1
    return None

def ledColHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    didDouble = 0
    matchingDevices = getDevicesFromAddress(addr)
    for i in range(len(stuff)):
        if i == 0:
            col = stuff[i]
            continue
        if didDouble == 1:
            didDouble = 0
            continue
        for device in matchingDevices:
            width = getWidth(device['type'], device['grids'])
	    height = getHeight(device['type'], device['grids'])
            colStartX = col - device['offsetX']
            colStartY = ((i - 1) * 8) - device['offsetY']
            if colStartX < 0 or colStartX >= width:
                continue
            if colStartY < 0 or colStartY >= height:
                continue
            if device['cable'] == "left" or device['cable'] == "right":
                fortyHCmd = 0x80
                seriesCmd = 0x50
                seriesDoubleCmd = 0x70
                deviceCol = adjustCableX(colStartX, device)
            else:
                fortyHCmd = 0x70
                seriesCmd = 0x40
                seriesDoubleCmd = 0x60
                deviceCol = adjustCableY(colStartX, device)
            if len(stuff) - i == 1 or device['type'] == "40h":
                if device['type'] == "40h":
                    b1 = fortyHCmd + deviceCol
                else:
                    b1 = seriesCmd + deviceCol
                b2 = stuff[i]
                device['device'].write(chr(b1) + chr(b2))
            else:
                b1 = chr(int(seriesDoubleCmd) + int(deviceCol))
                b2 = chr(stuff[i])
                b3 = chr(stuff[i+1])
                device['device'].write(str(b1) + str(b2) + str(b3))
                didDouble = 1
    return None

def frameHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    matchingDevices = getDevicesFromAddress(addr)
    
    if len(stuff) == 8:
        offsetX = 0
        offsetY = 0
        data = stuff
    if len(stuff) == 10:
        offsetX = stuff[0]
        offsetY = stuff[1]
        data = stuff[2:]
    for device in matchingDevices:
        width = getWidth(device['type'], device['grids'])
        height = getHeight(device['type'], device['grids'])
        myOffsetX = offsetX - device['offsetX']
        myOffsetY = offsetY - device['offsetY']
        for x in range(myOffsetX, 8 + myOffsetX):
            thisData = data[x - myOffsetX]
            if x >= width:
                continue;
            for y in range(myOffsetY, 8 + myOffsetY):
                if y >= height:
                    continue;
                bit = 2 ** (y - offsetY)
                act = thisData & bit
                if act > 0:
                    act = 1
                valX = adjustCableX(x, device)
                valY = adjustCableY(y, device)
                ledCmd(device, valX, valY, act)
    return None
    
def prefixHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    if len(stuff) == 1:
        for i,deviceInfo in enumerate(devices):
            devices[i]['prefix'] = stuff[0]
            initOscCallbacks(stuff[0])
    if len(stuff) == 2:
        if stuff[0] >= 0 and stuff[0] < len(devices):
            i = stuff[0]
            devices[i]['prefix'] = stuff[1]
            initOscCallbacks(stuff[1])
    return None

def offsetHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    if len(stuff) == 2:
        for i,deviceInfo in enumerate(devices):
            devices[i]['offsetX'] = stuff[0]
            devices[i]['offsetY'] = stuff[1]
    if len(stuff) == 3:
        if stuff[1] >= 0 and stuff[0] < len(devices):
            i = stuff[0]
            devices[i]['offsetX'] = stuff[1]
            devices[i]['offsetY'] = stuff[2]
    return None

def cableHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    if len(stuff) == 1:
        for i,deviceInfo in enumerate(devices):
            if devices[i]['type'] == "128":
                adjustedCable = adjust128Cable(stuff[0])
                devices[i]['cable'] = adjustedCable
            else:
                devices[i]['cable'] = stuff[0]
    if len(stuff) == 2:
        if stuff[1] >= 0 and stuff[0] < len(devices):
            i = stuff[0]
            if devices[i]['type'] == "128":
                adjustedCable = adjust128Cable(stuff[1])
                devices[i]['cable'] = adjustedCable
            else:
                devices[i]['cable'] = stuff[1]
    return None

def adjust128Cable(cable):
    if cable == "top":
        return "left"
    if cable == "right":
        return "top"
    if cable == "bottom":
        return "right"
    if cable == "left":
        return "bottom"
    return cable

def clearHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    matchingDevices = getDevicesFromAddress(addr)
    for device in matchingDevices:
        width = getWidth(device['type'], device['grids'])
        height = getHeight(device['type'], device['grids'])
        if device['type'] == "40h":
            for i in range(width):
                b1 = 0x70 + i
                b2 = 0
                device['device'].write(chr(b1) + chr(b2))
        else:
            b1 = (0x09 << 4) + stuff[0]
            device['device'].write(chr(b1))
    return None

def enableADCHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    matchingDevices = getDevicesFromAddress(addr)
    for device in matchingDevices:
        width = getWidth(device['type'], device['grids'])
        height = getHeight(device['type'], device['grids'])
        if device['type'] == "40h":
            b1 = 0x50
            b2 = stuff[0] << 4 + stuff[1]
            device['device'].write(chr(b1) + chr(b2))
        else:
            if stuff[1] == 1:
                b1 = 0xC0 + stuff[0]
            else:
                b1 = 0xD0 + stuff[0]
            device['device'].write(chr(b1))

def tiltmodeHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    matchingDevices = getDevicesFromAddress(addr)
    for i,device in enumerate(matchingDevices):
        devices[i]['tiltmode'] = stuff[0]
    enableADCHandler(addr, "ii", (0, stuff[0]), source)
    enableADCHandler(addr, "ii", (1, stuff[0]), source)

def intensityHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    if len(stuff) == 1:
        for deviceInfo in devices:
            if deviceInfo['type'] == "40h":
                b1 = 0x30
                b2 = stuff[0]
                deviceInfo['device'].write(chr(b1) + chr(b2))
            else:
                b1 = 0xA0 + stuff[0]
                deviceInfo['device'].write(chr(b1))
    if len(stuff) == 2:
        if stuff[1] >= 0 and stuff[0] < len(devices):
            i = stuff[0]
            if devices[i]['type'] == "40h":
                b1 = 0x30
                b2 = stuff[1]
                devices[i]['device'].write(chr(b1) + chr(b2))
            else:
                b1 = 0xA0 + stuff[1]
                devices[i]['device'].write(chr(b1))
    return None

def reportHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    msg = OSC.OSCMessage()
    msg.setAddress("/sys/devices")
    msg.append(len(devices))
    oscClient.send(msg)
    for i,deviceInfo in enumerate(devices):
        msg = OSC.OSCMessage()
        msg.setAddress("/sys/prefix")
        msg.append(i)
        msg.append(deviceInfo['prefix'])
        if debugMode == 1:
            print msg
        oscClient.send(msg)
    for i,deviceInfo in enumerate(devices):
        msg = OSC.OSCMessage()
        msg.setAddress("/sys/type")
        msg.append(i)
        msg.append(deviceInfo['type'])
        if debugMode == 1:
            print msg
        oscClient.send(msg)
    for i,deviceInfo in enumerate(devices):
        msg = OSC.OSCMessage()
        msg.setAddress("/sys/cable")
        msg.append(i)
        if deviceInfo['type'] == "128":
            msg.append(adjust128Cable(deviceInfo['cable']))
        else:
            msg.append(deviceInfo['cable'])
        if debugMode == 1:
            print msg
        oscClient.send(msg)
    for i,deviceInfo in enumerate(devices):
        msg = OSC.OSCMessage()
        msg.setAddress("/sys/serial")
        msg.append(i)
        msg.append(deviceInfo['serial'])
        if debugMode == 1:
            print msg
        oscClient.send(msg)
    for i,deviceInfo in enumerate(devices):
        msg = OSC.OSCMessage()
        msg.setAddress("/sys/offset")
        msg.append(i)
        msg.append(deviceInfo['offsetX'])
        msg.append(deviceInfo['offsetY'])
        if debugMode == 1:
            print msg
        oscClient.send(msg)
    return None

def testHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    for device in devices:
        if device['type'] == "40h":
            b1 = 0x40
            b2 = stuff[0]
            device['device'].write(chr(b1) + chr(b2))
        else:
            b1 = (0x09 << 4) + stuff[0]
            device['device'].write(chr(b1))
    return None
    
def gridsHandler(addr, tags, stuff, source):
    if debugMode == 1:
        print addr + " " + str(stuff)
    if len(stuff) == 1:
        for i,deviceInfo in enumerate(devices):
            devices[i]['grids'] = stuff[0]
            b1 = (0x0C << 4) + stuff[0]
            devices[i]['device'].write(chr(b1))
    if len(stuff) == 2:
        if stuff[1] >= 0 and stuff[0] < len(devices):
            i = stuff[0]
            devices[i]['grids'] = stuff[1]
            b1 = (0x0C << 4) + stuff[0]
            devices[i]['device'].write(chr(b1))
    return None

def initOscCallbacks(prefix):
    if debugMode == 1:
        print "initializing OSC callbacks for " + prefix
    oscServer.addMsgHandler(prefix + "/led", ledHandler)
    oscServer.addMsgHandler(prefix + "/led_row", ledRowHandler)
    oscServer.addMsgHandler(prefix + "/led_col", ledColHandler)
    oscServer.addMsgHandler(prefix + "/frame", frameHandler)
    oscServer.addMsgHandler(prefix + "/clear", clearHandler)
    oscServer.addMsgHandler(prefix + "/adc_enable", enableADCHandler)
    oscServer.addMsgHandler(prefix + "/tiltmode", tiltmodeHandler)

def init():
    deviceDescriptions = d2xx.listDevices(d2xx.OPEN_BY_DESCRIPTION)
    deviceSerials = d2xx.listDevices(d2xx.OPEN_BY_SERIAL_NUMBER)
    for i, description in enumerate(deviceDescriptions):
        serial = deviceSerials[i]
        if description[:6] != "monome" and description[:2] != "mk":
            print "ignoring non-monome device id " + str(i) + ": " + description + " [" + serial + "]"
            continue
        device = d2xx.open(i)
        print "opened device id " + str(i) + ": " + description + " [" + serial + "]"
        type = description[7:]
        grids = 0
        prefix = "/" + type
        initOscCallbacks(prefix)
        deviceInfo = {
            'description': description, 
            'serial': deviceSerials[i], 
            'prefix': prefix, 
            'type': type, 
            'device': device,
            'cable': "left",
            'offsetX': 0,
            'offsetY': 0,
            'tiltmode': 0,
            'grids': 0
        }
        if debugMode == 1:
            print deviceInfo
        devices.insert(i, deviceInfo)
        clearHandler(prefix, 'i', (0,), 0)
        thread = MonomeThread(deviceInfo, oscClient)
        thread.start();
        deviceInfo['thread'] = thread

devices = []
oscServer = OSC.OSCServer(listenAddr)
oscServer.addMsgHandler("/sys/prefix", prefixHandler)
oscServer.addMsgHandler("/sys/cable", cableHandler)
oscServer.addMsgHandler("/sys/offset", offsetHandler)
oscServer.addMsgHandler("/sys/intensity", intensityHandler)
oscServer.addMsgHandler("/sys/report", reportHandler)
oscServer.addMsgHandler("/sys/test", testHandler)
oscServer.addMsgHandler("/sys/grids", gridsHandler)
oscClient = OSC.OSCClient()
oscClient.connect(sendAddr)
init()
st = threading.Thread(target = oscServer.serve_forever)
st.start()