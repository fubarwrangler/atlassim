#!/usr/bin/python

from PyQt4 import QtGui, QtCore, uic
from simulation import Simulation
import layoutgen

import sys

colors = ('#00FF00', '#FF0000', '#E3CF57', '#0000FF', '#FF00FF', '#00FFFF',
          '#FFFF00', '#FFC0CB', '#C67171', '#000000')


class MainWindow(QtGui.QMainWindow, layoutgen.MainStats):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        uic.loadUi('ui/simulation.ui', self)

        self.sim = Simulation(400, submit_interval=300)
        self.sim.add_jobs()
        self.sim.farm.groups.update_quota(self.sim.farm)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.advance_interval)

        self.quitBtn.clicked.connect(self.close)
        self.stepBtn.clicked.connect(self.advance_interval)
        self.startStop.clicked.connect(self.toggle_run)
        self.simspeedSlider.valueChanged.connect(self.change_speed)
        self.to_plot = set(g.name for g in self.sim.farm.groups.active_groups())
        self.all_groups = self.sim.display_order()

        # ms between firing timer
        self.period = 350
        self.auto_run = False

        self.qedit = ManageQueues(self.sim)
        self.toolButton.clicked.connect(self.qedit.show)
        self.make_status_layout()

    def change_speed(self, val):

        self.simspeedSlider.setToolTip(str(val))
        self.simspeedLabel.setText('%dms delay' % val)
        self.period = val
        if self.auto_run:
            self.timer.start(val)

    def advance_interval(self):
        self.sim.step(self.stepSize.value())
        t = self.sim.farm.time
        st = 't=%d (n in %d, s in %d)' % (t,
             self.sim.next_negotiate - t, self.sim.next_submit - t)
        self.timeLabel.setText(st)
        for grp, lbl in self._stat_labels.items():
            group = self.sim.farm.groups.get_by_name(grp)
            lbl.setText(self._format_grpstr(group))
        self.update_plot()

    def update_plot(self):
        x, y = self.sim.make_plotdata(self.to_plot)
        self.mpl.canvas.ax.cla()
        self.mpl.canvas.ax.stackplot(x, y, colors=self.gen_color(), baseline='zero')
        self.mpl.canvas.draw()

    def gen_color(self):
        for n, grp in enumerate(self.all_groups):
            if grp in self.to_plot:
                yield colors[n]

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
