#!/usr/bin/python

from computefarm import COMPLETED, IDLE, RUNNING


class BatchJob(object):
    """ Class representing one job for the batch system """

    def __init__(self, cpus=1, memory=None, group="grid", length=3600):

        self.cpus = cpus if cpus else 1
        self.memory = memory if memory is not None else self.cpus * 2000
        self.group = group
        self.length = length

        self.current_node = None
        self.slotid = None
        self.state = IDLE
        self.runtime = 0
        self.queue = None

    def advance_time(self, step):
        self.runtime += step
        if self.runtime >= self.length:
            self.state = COMPLETED
            self.queue.remove(self)

    def state_char(self):
        return ['I', 'R', 'C'][self.state]

    def __str__(self):
        x = "%s: %d CPU %d Mb" % (self.group, self.cpus, self.memory)
        if self.state == RUNNING:
            x = "slot%d " % self.slotid + x
        return x

    def long(self):
        s = "%2d-core  %5dMb  %10s   %s" % (self.cpus, self.memory, self.group,
                                            self.state_char())
        if self.current_node and self.slotid is not None:
            s += "   (%s@%s)" % (self.slotid, self.current_node)
        return s
