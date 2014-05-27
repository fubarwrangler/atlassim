#!/usr/bin/python

from PyQt4 import QtGui, QtCore, uic
from simulation import Simulation
import layoutgen

import sys

colors = ('#00FF00', '#FF0000', '#E3CF57', '#0000FF', '#FF00FF', '#00FFFF',
          '#FFFF00', '#FFC0CB', '#C67171', '#000000')


class MainWindow(QtGui.QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('ui/simulation.ui', self)

        self.sim = Simulation(400, submit_interval=300)
        self.sim.add_jobs()
        self.sim.farm.groups.calc_quota(self.sim.farm)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advance_interval)

        self.quitBtn.clicked.connect(self.close)
        self.stepBtn.clicked.connect(self.advance_interval)
        self.startStop.clicked.connect(self.toggle_run)
        self.simspeedSlider.valueChanged.connect(self.change_speed)

        # ms between firing timer
        self.period = 350
        self.auto_run = False

        self.qedit = ManageQueues(self.sim)
        self.toolButton.clicked.connect(self.qedit.show)
        self.make_status_layout()

    def _format_grpstr(self, grp):
        idle = self.sim.farm.queue.get_group_idle(grp.name)
        run = self.sim.farm.queue.get_group_running(grp.name)
        return '%s (q=%d,s=%s): (run/idle) %d/%d' % \
               (grp.name, grp.norm_quota, grp.surplus, run, idle)

    def make_status_layout(self):
        self._stat_labels = {}
        for grp in self.sim.farm.groups.active_groups():

            lbl = QtGui.QLabel(self._format_grpstr(grp))
            lbl.setObjectName('grpStatInfo_%s' % grp.name)
            self._stat_labels[grp.name] = lbl
            self.statusLayout.addWidget(lbl)

    def change_speed(self, val):

        self.simspeedSlider.setToolTip(str(val))
        self.simspeedLabel.setText('%dms delay' % val)
        self.period = val
        if self.auto_run:
            self.timer.start(val)

    def advance_interval(self):
        self.sim.step(self.stepSize.value())
        self.timeLabel.setText('t=%d' % self.sim.farm.time)
        for grp, lbl in self._stat_labels.items():
            group = self.sim.farm.groups.get_by_name(grp)
            lbl.setText(self._format_grpstr(group))
        self.update_plot()

    def update_plot(self):
        x, y = self.sim.make_plotdata()
        self.mpl.canvas.ax.cla()
        self.mpl.canvas.ax.stackplot(x, y, colors=colors, baseline='zero')
        self.mpl.canvas.draw()

    def toggle_run(self):
        if self.auto_run:
            self.timer.stop()
            self.startStop.setText('Run')
            self.auto_run = False
        else:
            self.timer.start(self.period)
            self.startStop.setText('Pause')
            self.auto_run = True


class ManageQueues(QtGui.QDialog, layoutgen.QueueManage):

    def __init__(self, simulation, parent=None):
        super(ManageQueues, self).__init__(parent)
        uic.loadUi('ui/queue_dialog.ui', self)
        self.closeButton.clicked.connect(self.close)
        self.sim = simulation
        self.sliders = {}

        self.add_controls()


if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
