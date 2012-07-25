####
# client.py
# author: tom dinchak (dinchak@gmail.com)
#
# this file contains a few examples on how to configure monomeserial at runtime.
# please modify it to fit your needs.  see the OSC specification for reference:
#
# http://docs.monome.org/doku.php?id=tech:protocol:osc
#
# when you start monomeserial.py you will see a line like this:
#
# opened device id 0: monome 128 [m128-302]
#
# you use the device ids to direct /sys/cable, /sys/prefix, etc. messages to a
# specific monome.  omitting the device id will cause the message to be sent to
# all monomes as outlined in the OSC specification.
#
# you need to uncomment the msg code below (remove the # signs in front of each 
# line).  one full message looks like this:
#
# msg = OSC.OSCMessage()
# msg.setAddress("/sys/cable")
# msg.append(0)
# msg.append("top");
# client.send(msg)
#
# make sure you initialize a new OSC.OSCMessage() for each one and that you append 
# each argument separately.  msg.setAddress("/sys/cable 0 top") will not work.
# msg.append("0 top") will not work.
#
# once you have configured your client.py you just need to run it (double click).
# it will flash a console window quickly and then close, monomeserial should be
# configured at that point.
#
# visit the monome formus if you have questions.
# 
####

import OSC
import time

serverAddr = "localhost", 8080
client = OSC.OSCClient()
client.connect(serverAddr)

###
#
# send a "/sys/cable 0 top" message.  this sets the
# cable orientation of the device at id 0 to "top".
#
#msg = OSC.OSCMessage()
#msg.setAddress("/sys/cable")
#msg.append(0)
#msg.append("top");
#client.send(msg)
#
###

###
#
# send a "/sys/offset 0 0 8" message.  this sets the
# offset of the device at id 0 to x=0, y=8 (down 8 rows).
#
#msg = OSC.OSCMessage()
#msg.setAddress("/sys/offset")
#msg.append(0);
#msg.append(0);
#msg.append(8)
#client.send(msg)
#
###

###
#
# send a "/sys/grids 1" message to enable a mk-64 kit.
# change 1 to 2 for a 128.  change 1 to 4 for a 256.
#
#msg = OSC.OSCMessage()
#msg.setAddress("/sys/grids")
#msg.append(1)
#client.send(msg)
#
###

