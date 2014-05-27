#!/usr/bin/python

import computefarm as cf
from computefarm.farm import depth_first
import random
import logging

import numpy as np


HOUR = 60 * 60

default_queue_properties = {
    'grid':     { 'num': 2, 'mem': 750, 'avg': HOUR, 'std': 0.6 * HOUR},
    'prod':     { 'num': 0, 'avg': 8 * HOUR, 'std': 3 * HOUR},
    'short':    { 'num': 0, 'avg': 1.2 * HOUR, 'std': 300},
    'long':     { 'num': 0, 'avg': 16 * HOUR, 'std': 3 * HOUR},
    'test':     { 'num': 0, 'avg': 8 * HOUR, 'cpu': 3},
    'mp8':      { 'num': 0, 'avg': 6 * HOUR, 'std': 4 * HOUR, 'cpu': 8, 'mem': 6000}
}

log = logging.getLogger('sim')


class Simulation(object):

    def __init__(self, cores, negotiate_interval=150, stat_freq=10, submit_interval=200):

        self.farm = cf.Farm()
        dist = (
            (24, 331),
            (32, 90),
            (8, 238),
        )
        self.farm.generate_from_dist(dist, size=cores)

        root = self.setup_groups(cf.Group('<root>'))
        self.farm.attach_groups(root)
        self._init_stat(stat_freq * 100)

        self.farm.set_negotiatior_rank(depth_first)

        self.queue = cf.JobQueue()
        self.farm.attach_queue(self.queue)

        # How many seconds per negotiation/stat gathering cycle
        self.int_stat = stat_freq
        self.int_negotiate = negotiate_interval
        self.int_submit = submit_interval
        self.next_stat = 0
        self.next_negotiate = 0
        self.next_submit = 0

        # How many seconds to simulate each step
        self.sec_per_step = 5

    def _init_stat(self, hist_size):
        self._stat = {}
        self._stat_size = hist_size
        for x in self.farm.groups.active_groups():
            self._stat[x.name] = np.zeros((hist_size), int)

    def _update_stat(self):
        usage = self.farm.get_usage()
        for g in (x.name for x in self.farm.groups.active_groups()):
            self._stat[g] = np.roll(self._stat[g], -1)
            self._stat[g][-1] = usage[g]

    def setup_groups(self, root):
        root.add_child('atlas')
        root.add_child('grid', 0.3)
        root['atlas'].add_child('production')
        root['atlas'].add_child('analysis')
        root['atlas']['production'].add_child('prod', 6)
        root['atlas']['production'].add_child('mp8', 9)
        root['atlas']['production'].add_child('test', 9)
        root['atlas']['analysis'].add_child('short', 7)
        root['atlas']['analysis'].add_child('long', 5)

        for x in root.walk():
            if x.name in default_queue_properties:
                x.set_character(**default_queue_properties[x.name])
        return root

    def add_jobs(self):
        for group in self.farm.groups.active_groups():
            num_submit = group.num - self.farm.queue.get_group_idle(group.name)
            if num_submit <= 0:
                continue
            log.info("Submitting %d more %s jobs", num_submit, group.name)
            for n in xrange(num_submit):
                length = abs(random.gauss(group.avg, group.std))
                job = cf.BatchJob(group=group.name, cpus=group.cpu, memory=group.mem,
                                  length=length)
                self.queue.add_job(job)

    def step(self, dt):

        for i in xrange(dt):

            self.farm.advance_time(self.sec_per_step)

            if self.farm.time > self.next_submit:
                self.add_jobs()
                self.next_submit = self.farm.time + self.int_submit

            if self.farm.time > self.next_negotiate:
                self.farm.negotiate_jobs()
                self.next_negotiate = self.farm.time + self.int_negotiate

            if self.farm.time > self.next_stat:
                self._update_stat()
                self.next_stat = self.farm.time + self.int_stat

    def display_order(self):
        return sorted(self._stat.keys())

    def make_plotdata(self, groups='all'):

        x = np.arange(self._stat_size)
        if groups == 'all':
            y = np.vstack((v for k, v in sorted(self._stat.iteritems())))
        else:
            y = np.vstack((v for k, v in sorted(self._stat.iteritems()) if k in groups))

        return x, y


if __name__ == '__main__':

    s = Simulation()
