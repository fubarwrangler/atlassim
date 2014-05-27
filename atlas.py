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

    def change_speed(self, val):

        self.simspeedSlider.setToolTip(str(val))
        self.simspeedLabel.setText('%dms delay' % val)
        self.period = val
        if self.auto_run:
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

        self.add_controls()

    def add_controls(self):
        active_groups = set([x.name for x in self.sim.farm.groups.active_groups()])
        self.controls = {}
        regex = QtCore.QRegExp("^[0-9]+$")

        for g in self.sim.farm.groups.walk():
            active = g.name in active_groups
            c = {}

            new_layout = QtGui.QVBoxLayout()
            label = QtGui.QLabel(g.name, self)
            surplus = QtGui.QCheckBox("Surplus", self)
            new_layout.addWidget(label)
            if active:
                slider = QtGui.QSlider(self)
                slider.setObjectName("slider_%s" % g.name)
                slider.setValue(g.num)
                slider.valueChanged.connect(self.slider_changed)

                value_label = QtGui.QLabel(str(slider.value()), self)
                value_label.setObjectName("valLabel_%s" % g.name)
                quota_edit = QtGui.QLineEdit(str(g.norm_quota), self)
                quota_edit.setValidator(QtGui.QRegExpValidator(regex, quota_edit))
                new_layout.addWidget(slider)
                new_layout.addWidget(value_label)
                new_layout.addWidget(quota_edit)
                c['valueLabel'] = value_label
                c['quotaEdit'] = quota_edit
                c['slider'] = slider

            c['surplusBox'] = surplus
            new_layout.addWidget(surplus)
            self.slidersLayout.addLayout(new_layout)
            self.controls[g.name] = c

        #for name, slider in self.sliders.items():
            #slider.valueChanged.connect(self.update_)

    @staticmethod
    def extract_group(sender):
        return str(sender.objectName()).split("_")[-1]

    def slider_changed(self, demand):
        group_name = self.extract_group(self.sender())
        self.controls[group_name]['valueLabel'].setText(str(demand))
        group = self.sim.farm.groups.get_by_name(group_name)
        group.num = demand




if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
