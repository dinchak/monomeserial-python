monomeserial-python
===================

A monomeserial implementation in Python.  Uses a Windows-only USB/Serial library but that should be pretty easy to replace.  This used to serve a purpose for me but since serialosc it should no longer be needed.

The last time I used it, I used Python 2.6.5 and PyUSB 1.6.  Newer versions should probably be fine.

PyUSB: http://www.bleyer.org/pyusb/

Once that is installed just run monomeserial.py.  If you want to configure it (cable orientation, offset, etc.) then you'll have to send it some OSC messages.  The client.py file contains a few examples on how to do this.