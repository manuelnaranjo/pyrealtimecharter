#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
    Copyright 2010 Naranjo, Manuel Francisco <manuel@aircable.net>

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

Based on one of the matplot examples, this will draw received data from the
serial port on real time.
"""

import os, sys, random, select, termios, fcntl, serial

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas

from PyQt4 import QtCore, QtGui

import numpy as np
import time

SPAN=60 # last X seconds

def scan():
    """scan for available ports. return a list of tuples (num, name)"""
    available = []
    for i in range(256):
        try:
            s = serial.Serial(i)
            available.append((i, s.portstr))
            s.close()   # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
    if os.name == 'posix':
      for i in range(256):
        try:
            s = serial.Serial('/dev/ttyUSB%s' % i)
            available.append( (i, s.portstr) )
            s.close()   # explicit close 'cause of delayed GC in java
        except serial.SerialException:
            pass
    return available


class BlitQT(FigureCanvas):

    def addSerie(self, serie):
        ind = len(self.series)+1
        plot = self.figure.add_subplot( ind, 1, ind )
        plot.autoscale(enable=True, tight=True)
        plot.set_ylabel(serie)
        plot.set_xlim(left=self.tstart)
        plot.grid()

        self.series[serie] = {
    	    'plot': plot,
	    'x':[],
	    'y':[],
	    'background': self.copy_from_bbox(plot.bbox),
	    'chart': plot.plot([],[])[0]
	}

	i=1
	for s in self.series:
	    if s == serie:
		continue
	    self.figure.delaxes(self.series[s]['plot'])
	    plot = self.figure.add_subplot( ind, 1, i)
    	    plot.autoscale(enable=True, tight=True)
    	    plot.set_ylabel(s)
    	    plot.grid()
    	    self.series[s]['plot']=plot
	    self.series[s]['background'] = self.copy_from_bbox(plot.bbox)
	    self.series[s]['chart']=plot.plot([],[])[0]
	    i+=1
	self.draw()

    def addDataPoint(self, serie, value):
	if serie not in self.series:
	    # no conozco serie, agregar
	    self.addSerie(serie)

	plot = self.series[serie]
	self.lasttime = time.time()
	plot['x'].append(self.lasttime)
	plot['y'].append(value)
	plot['chart'].set_xdata(plot['x'])
	plot['chart'].set_ydata(plot['y'])
	if len(plot['x']) == 0:
	    return
	m = min(plot['y'])*0.9
	M = max(plot['y'])*1.1
	if m != M:
	    plot['plot'].set_ylim(m, M)

    def updateSpan(self):
	now = time.time()
	for s in self.series:
	    self.series[s]['plot'].set_xlim(now-SPAN, now)

    def keyPressEvent(self, event):
	key = event.key()
	if key == QtCore.Qt.Key_Escape:
	    self.close
	    return
	print key, chr(key)
	self.port.write('%s' % chr(key))

    def __init__(self, port):
        FigureCanvas.__init__(self, Figure())
        self.series = dict()
        self.draw()
        self.tstart = time.time()
        self.startTimer(500)
        self.port = serial.Serial(port, timeout=0.01)
        self.lasttime = 0
        self.cnt = 0

	# vaciar buffer
	if len(select.select([self.port,],[],[], 0)[0]) > 0:
	    self.port.flush()

    def timerEvent(self, event):
	self.cnt+=1

	# ver si hay algo en el puerto
	if len(select.select([self.port,],[],[], 0)[0]) == 0:
	    self.doRedraw()
	    return

	for line in self.port.readlines():
	    line=line.strip()
	    if len(line) == 0:
		continue
	    try:
		serie, dato = line.split(';')[:2]
		dato = float(dato)
		self.addDataPoint(serie, dato)
	    except Exception, err:
		pass
	self.doRedraw()

    def resizeEvent(self, event):
	for i in self.series:
	    self.series[i]['background']=self.copy_from_bbox(self.series[i]['plot'].bbox)
	super(BlitQT, self).resizeEvent(event)

    def doRedraw(self):
	self.updateSpan()
	self.draw()
	for i in self.series:
	    pl = self.series[i]
	    # clear!
	    self.restore_region(['background'])
	    # update chart
	    pl['plot'].draw_artist(pl['chart'])
	    # plot axis
	    self.blit(pl['plot'].bbox)
	self.draw()


if __name__=='__main__':
    i = 0
    ports = scan()
    if len(ports) == 0 and len(sys.argv) == 1:
	print "Couldn't found port, please give me a port name as argument"
	sys.exit(0)

    if len(sys.argv) == 1:
	print "Choose port:"
	for num, port in ports:
	    print "\t %i: %s" % (i, port)
	    i+=1
	port = int(raw_input("enter number: "))
	port = ports[port][1]
    else:
	port = sys.argv[1]

    app = QtGui.QApplication(sys.argv)
    widget = BlitQT(port)
    widget.show()

    sys.exit(app.exec_())
