#!/usr/bin/python

import computefarm as cf
from computefarm.farm import depth_first
import random

import matplotlib.pyplot as plt
import numpy as np


HOUR = 60 * 60

default_queue_properties = {
    'grid':     {'memory': 750, 'len': HOUR, 'std': 0.6 * HOUR},
    'prod':     {'len': 8 * HOUR, 'std': 3 * HOUR},
    'short':    {'len': 1.2 * HOUR, 'std': 300},
    'long':     {'len': 16 * HOUR, 'std': 3 * HOUR},
    'test':     {'len': 8 * HOUR, 'cpu': 3},
    'mp8':      {'len': 6 * HOUR, 'std': 4 * HOUR, 'cpu': 8, 'memory': 6000}
}


class Simulation(object):

    def __init__(self, cores, negotiate_interval=150, stat_freq=10):

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
        self.next_stat = 0
        self.next_negotiate = 0

        # How many seconds to simulate each step
        self.sec_per_step = 10

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
        return root

    def add_jobs(self, jdf_map):
        for group, data in jdf_map.items():
            info = default_queue_properties[group]
            info.update(data)

            cpu = info.get('cpu')
            mem = info.get('memory')
            avglen = info.get('len', 3600)
            stddev = info.get('std', avglen / 6)
            for n in xrange(info.get('count', 1)):
                length = abs(random.gauss(avglen, stddev))
                job = cf.BatchJob(group=group, cpus=cpu, memory=mem,
                                  length=length)
                self.queue.add_job(job)

    def step(self, dt):

        for i in xrange(dt):

            self.farm.advance_time(self.sec_per_step)

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
            y = np.vstack((v for k,v in sorted(self._stat.iteritems())))
        else:
            y = np.vstack((x[1] for x in sorted(self._stat.iteritems())))

        return x, y


if __name__ == '__main__':

    s = Simulation()
