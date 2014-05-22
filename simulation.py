#!/usr/bin/python

import computefarm as cf
from computefarm.farm import depth_first
import stats as st
import random

import matplotlib.pyplot as plt
import numpy as np


class Simulation(object):

    def __init__(self, negotiate_interval=150):

        self.farm = cf.Farm()
        dist = (
            (24, 40),
            (32, 20),
            (8, 10),
        )
        self.farm.generate_from_dist(dist, size=200)

        root = self.setup_groups(cf.Group('<root>'))
        st.make_groups(root, 2600)
        self.farm.attach_groups(root)

        self.farm.set_negotiatior_rank(depth_first)

        self.queue = cf.JobQueue()
        self.farm.attach_queue(self.queue)

        self.int_stat = 5
        self.int_negotiate = negotiate_interval
        self.next_stat = 1
        self.next_negotiate = 0

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
        sample_map = {
            'grid':     {'count': 20, 'cpu': 1, 'memory': 750, 'len': 3500, 'std': 2000},
            'prod':     {'count': 102},
            'short':    {'count': 82},
            'long':     {'count': 55},
            'test':     {'count': 55, 'cpu': 3},
            'mp8':      {'count': 14, 'cpu': 8, 'memory': 6000}
        }

        for group, info in sample_map.items():
            cpu = info.get('cpu')
            mem = info.get('memory')
            avglen = info.get('len', 3600)
            stddev = info.get('std', 1200)
            for n in xrange(info.get('count', 1)):
                length = abs(random.gauss(avglen, stddev))
                job = cf.BatchJob(group=group, cpus=cpu, memory=mem,
                                  length=length)
                self.queue.add_job(job)

    def _update_accounting(self):
        usage = self.farm.get_usage()
        for g in (x.name for x in self.farm.groups.active_groups()):
            st.push_data(g, usage[g])

    def step(self, dt):

        for i in xrange(dt):

            self.farm.advance_time(1)

            if self.farm.time > self.next_negotiate:
                self.farm.negotiate_jobs()
                self.next_negotiate = self.farm.time + self.int_negotiate

            if self.farm.time > self.next_stat:
                self._update_accounting()
                self.next_stat = self.farm.time + self.int_stat

    def plot(self):

        plt.stackplot(np.arange(st.get_size()), np.vstack((x[1] for x in st.get_groups())),
              colors=('#00FF00', '#FF0000', '#E3CF57', '#0000FF', '#FF00FF', '#00FFFF',
                      '#FFFF00', '#FFC0CB', '#C67171', '#000000'))
        plt.show()


if __name__ == '__main__':

    s = Simulation()
