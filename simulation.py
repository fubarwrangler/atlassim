#!/usr/bin/python

import computefarm as cf
from computefarm.farm import depth_first, breadth_first
import random
import logging

import numpy as np


HOUR = 60 * 60

default_queue_properties = {
    'grid':     { 'num': 0,  'mem': 750, 'avg': HOUR, 'std': 0.6 * HOUR},
    'prod':     { 'num': 0,  'avg': 8 * HOUR, 'std': 3 * HOUR},
    'short':    { 'num': 500, 'avg': 1.2 * HOUR, 'std': 600},
    'long':     { 'num': 500,  'avg': 5 * HOUR, 'std': 2 * HOUR},
    'test':     { 'num': 0,  'avg': 8 * HOUR, 'cpu': 3},
    'mp8':      { 'num': 0,  'avg': 6 * HOUR, 'std': 4 * HOUR, 'cpu': 8, 'mem': 6000}
}


def sort_like(array, like):
    # All items in @like are picked in order if they exist in the array
    for x in like:
        if x in array:
            yield x
    # All the remaining are picked here
    for x in sorted(set(array) - set(like)):
        yield x

log = logging.getLogger('sim')


class Simulation(object):

    def __init__(self, nodes, negotiate_interval=150, stat_freq=10, submit_interval=200):
        """ Initialize the farm simulation, attach groups and queues to it and
            provide method of submitting jobs of a predetermined size into the
            queues.
        """

        self.farm = cf.Farm()

        # Distribution of farm nodes, e.g. 331/90 is ratio of 24/32 core machines
        dist = (
            (24, 331),
            (32, 90),
            (8, 238),
        )
        self.farm.generate_from_dist(dist, size=nodes)

        root = self.setup_groups(cf.Group('<root>'))
        self.farm.attach_groups(root)
        self._init_stat(stat_freq * 100)

        #Default ranking
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

    # these two _set* knobs are used in callbacks by the GUI
    def _set_neg_df(self):
        self.farm.set_negotiatior_rank(depth_first)

    def _set_neg_bf(self):
        self.farm.set_negotiatior_rank(breadth_first)

    def _init_stat(self, hist_size):
        """ Statistics are kept in a constant-size numpy array that is updated
            periodically
        """

        self._stat = {}
        self._stat_size = hist_size
        for x in self.farm.groups.active_groups():
            self._stat[x.name] = np.zeros((hist_size), int)

    def _update_stat(self):
        usage = self.farm.get_usage()
        for g in (x.name for x in self.farm.groups.active_groups()):
            # Left-shift entire array back by one, so element n -> element n - 1
            self._stat[g] = np.roll(self._stat[g], -1)
            # New last element is current update
            self._stat[g][-1] = usage[g]

    def setup_groups(self, root):
        """ Reflects current ATLAS group structure:

         /- atlas +-- production +-- prod
         |        |              |
         |        |              \-- mp8
         |        |              |
         |        |              \-- test
  <root>-+        |
         |        \-- analysis +-- short
         |                     |
         |                     \-- long
         \- grid

        """

        root.add_child('atlas')
        root.add_child('grid', 3)
        root['atlas'].add_child('production')
        root['atlas'].add_child('analysis')
        root['atlas']['production'].add_child('prod', 40)
        root['atlas']['production'].add_child('mp8', 5)
        root['atlas']['production'].add_child('test', 7)
        root['atlas']['analysis'].add_child('short', 10)
        root['atlas']['analysis'].add_child('long', 10)

        # Populate with default properties from top of this module
        for x in root.walk():
            if x.name in default_queue_properties:
                x.set_character(**default_queue_properties[x.name])
        return root

    def add_jobs(self):
        """ Submit more jobs into the queue, keeping the total idle jobs where
            they should be according to the sliders in the GUI.
        """

        for group in self.farm.groups.active_groups():
            num_submit = group.num - self.farm.queue.get_group_idle(group.name)

            if num_submit <= 0:
                continue

            log.info("Submitting %d more %s jobs", num_submit, group.name)

            for n in xrange(num_submit):
                # Job length is random within a Gaussian distribution
                length = abs(random.gauss(group.avg, group.std))

                # Create job object and add it to queue
                job = cf.BatchJob(group=group.name, cpus=group.cpu, memory=group.mem,
                                  length=length)
                self.queue.add_job(job)

    def step(self, dt):
        """ Advance time of the simulation by dt steps at a time, making next
            submission/negotiation/statistics-gathering as appropriate
        """

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
        sort_order = ('short', 'long', 'test', 'prod', 'mp8')
        return list(sort_like(self._stat.keys(), sort_order))

    def make_plotdata(self, groups='all'):

        x = np.arange(self._stat_size)
        if groups == 'all':
            y = np.vstack((self._stat[x] for x in self.display_order()))
        else:
            y = np.vstack((self._stat[x] for x in self.display_order() if x in groups))

        return x, y


if __name__ == '__main__':

    s = Simulation()
