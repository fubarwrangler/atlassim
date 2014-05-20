#!/usr/bin/python

import numpy as np


g_data = dict()


def make_groups(groups, depth=10):
    for x in groups.active_groups():
        #g_data[x] = collections.deque(maxlen=depth)
        g_data[x.name] = np.zeros((depth), int)


def push_data(group, usage):
    g_data[group] = np.roll(g_data[group], -1)
    g_data[group][-1] = usage


def get_data(group):
    return g_data[group]


def get_groups():
    return sorted(g_data.iteritems())


def get_size():
    return len(g_data[g_data.keys()[0]])
