#!/usr/bin/python

import collections


g_data = dict()


def make_groups(groups):
    for x in groups:
        g_data[x] = collections.deque(maxlen=10)


def push_data(group, usage):
    g_data[group].append(usage)


def get_data(group):
    return g_data[group]
