# -*- coding: utf-8 -*-
"""
Demonstrates a way to put multiple axes around a single plot. 

(This will eventually become a built-in feature of PlotItem)

"""
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

pg.mkQApp()

pw = pg.PlotWidget()
pw.show()
pw.setWindowTitle('pyqtgraph example: MultiplePlotAxes')
p1 = pw.getPlotItem()



## create a new ViewBox, link the right axis to its coordinate system
p2 = pg.ViewBox()
p1.showAxis('right')
p1.scene().addItem(p2)
p1.getAxis('right').linkToView(p2)
p2.setXLink(p1)
p1.getAxis('left').setLabel('axis1', color='#0000ff')
p1.getAxis('right').setLabel('axis2', color='g')


## Handle view resizing 
def updateViews():
    ## view has resized; update auxiliary views to match
    global p1, p2
    p2.setGeometry(p1.vb.sceneBoundingRect())
    p2.linkedViewChanged(p1.vb, p2.XAxis)


def _rise_auto_button(self):
    global p1
    p1.vb.disableAutoRange()
    p1.showButtons()

def _auto_button_signal():
    global p2
    p2.enableAutoRange()

updateViews()
p1.vb.sigResized.connect(updateViews)
p2.sigRangeChangedManually.connect(_rise_auto_button)
p1.autoBtn.clicked.connect(_auto_button_signal)

p1.plot([1, 2, 4, 8, 16, 32])
p2.addItem(pg.PlotCurveItem([10, 20, 40, 80, 40, 20], pen='b'))

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()