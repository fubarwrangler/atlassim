#!/usr/bin/python

from PyQt4 import QtGui, uic

import sys

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    mw = uic.loadUi('ui/simulation.ui', package='.ui')
    #mw = MainWindow()
    mw.show()
    sys.exit(app.exec_())