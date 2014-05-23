#!/usr/bin/python

from PyQt4 import QtGui, QtCore, uic
from simulation import Simulation

import sys

colors = ('#00FF00', '#FF0000', '#E3CF57', '#0000FF', '#FF00FF', '#00FFFF',
          '#FFFF00', '#FFC0CB', '#C67171', '#000000')


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('ui/simulation.ui', self)

        self.sim = Simulation(400, submit_interval=10000)
        self.sim.add_jobs()

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advance_interval)

        self.quitBtn.clicked.connect(self.close)
        self.stepBtn.clicked.connect(self.advance_interval)
        self.startStop.clicked.connect(self.toggle_run)
        self.simspeedSlider.valueChanged.connect(self.print_data)

        # ms between firing timer
        self.period = 350
        self.auto_run = False

        self.qedit = ManageQueues(self.sim)
        self.toolButton.clicked.connect(self.qedit.show)

    def print_data(self, val):

        self.simspeedSlider.setToolTip(str(val))
        self.simspeedLabel.setText('%dms delay' % val)
        self.period = val
        self.timer.start(val)

    def advance_interval(self):
        self.sim.step(self.stepSize.value())
        self.timeLabel.setText('t=%d' % self.sim.farm.time)
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
            self.timer.start(self.period)
            self.startStop.setText('Stop')
            self.auto_run = True


class ManageQueues(QtGui.QDialog):

    def __init__(self, simulation, parent=None):
        super(ManageQueues, self).__init__(parent)
        uic.loadUi('ui/queue_dialog.ui', self)
        self.closeButton.clicked.connect(self.close)
        self.sim = simulation
        self.sliders = {}

        self.add_sliders()

    def add_sliders(self):
        for g in self.sim.farm.groups.active_groups():

            new_layout = QtGui.QVBoxLayout()
            slider = QtGui.QSlider(self)
            label = QtGui.QLabel(g.name, self)
            value_label = QtGui.QLabel(str(slider.value()), self)

            new_layout.addWidget(value_label)
            new_layout.addWidget(slider)
            new_layout.addWidget(label)
            self.slidersLayout.addLayout(new_layout)
            #slider.valueChanged.connect(self.update_group)
            self.sliders[g.name] = slider

        #for name, slider in self.sliders.items():
            #slider.valueChanged.connect(self.update_)


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
