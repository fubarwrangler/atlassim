#!/usr/bin/python

from PyQt4 import QtGui, uic
from simulation import Simulation

import sys


class MainWindow(QtGui.QMainWindow):

    ssi = 0

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        super(MainWindow, self).__init__(parent)
        uic.loadUi('ui/simulation.ui', self)

        self.sim = Simulation()

        self.quitBtn.clicked.connect(self.close)
        self.startstop.clicked.connect(self.toggle_text)

    def toggle_text(self):
        MainWindow.ssi = (MainWindow.ssi  + 1) % 2
        self.startstop.setText(['Run', 'Stop'][MainWindow.ssi])


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
