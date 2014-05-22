#!/usr/bin/python

from PyQt4 import QtGui, QtCore, uic
from simulation import Simulation

import sys

sample_map = {
    'grid':     {'count': 20, 'cpu': 1, 'memory': 750, 'len': 3500, 'std': 2000},
    'prod':     {'count': 102},
    'short':    {'count': 82},
    'long':     {'count': 55},
    'test':     {'count': 55, 'cpu': 2},
    'mp8':      {'count': 14, 'cpu': 8, 'memory': 6000}
}

colors = ('#00FF00', '#FF0000', '#E3CF57', '#0000FF', '#FF00FF', '#00FFFF',
          '#FFFF00', '#FFC0CB', '#C67171', '#000000')


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        super(MainWindow, self).__init__(parent)
        uic.loadUi('ui/simulation.ui', self)

        self.sim = Simulation(400)
        self.sim.add_jobs(sample_map)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advance_interval)

        self.quitBtn.clicked.connect(self.close)
        self.stepBtn.clicked.connect(self.advance_interval)
        self.startStop.clicked.connect(self.toggle_run)

        self.auto_run = False

    def advance_interval(self):
        self.sim.step(self.stepSize.value())
        self.update_plot()

    def update_plot(self):
        x, y = self.sim.make_plotdata()
        self.mpl.canvas.ax.cla()
        self.mpl.canvas.ax.stackplot(x, y, colors=colors)
        self.mpl.canvas.draw()

    def toggle_run(self):
        if self.auto_run:
            self.timer.stop()
            self.startStop.setText('Run')
            self.auto_run = False
        else:
            self.timer.start(350)
            self.startStop.setText('Stop')
            self.auto_run = True


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
