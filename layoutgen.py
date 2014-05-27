#!/usr/bin/python

from PyQt4 import QtGui, QtCore


class QueueManage(object):

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
            surplus.setObjectName('surplusBox_%s' % g.name)
            surplus.setCheckState(2 if g.surplus else 0)
            surplus.stateChanged.connect(self.set_surplus)
            new_layout.addWidget(label)
            if active:
                slider = QtGui.QSlider(self)
                slider.setObjectName("slider_%s" % g.name)
                slider.setValue(g.num)
                slider.valueChanged.connect(self.slider_changed)
                slider.setMaximum(500)
                slider.setPageStep(500)

                value_label = QtGui.QLabel(str(slider.value()), self)
                value_label.setObjectName("valLabel_%s" % g.name)

                quota_edit = QtGui.QLineEdit(str(g.quota), self)
                quota_edit.setObjectName("editQuota_%s" % g.name)
                quota_edit.setValidator(QtGui.QRegExpValidator(regex, quota_edit))
                quota_edit.textEdited.connect(self.quota_changed)

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

    @staticmethod
    def extract_group(sender):
        return str(sender.objectName()).split("_")[-1]

    def slider_changed(self, demand):
        group_name = self.extract_group(self.sender())
        self.controls[group_name]['valueLabel'].setText(str(demand))
        group = self.sim.farm.groups.get_by_name(group_name)
        group.num = demand

    def quota_changed(self, val):
        group = self.sim.farm.groups.get_by_name(self.extract_group(self.sender()))
        group.quota = int(val)

    def set_surplus(self, state):
        group = self.sim.farm.groups.get_by_name(self.extract_group(self.sender()))
        group.surplus = bool(state)
