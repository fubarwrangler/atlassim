#!/usr/bin/python

import pprint


class Groups(object):

    def __init__(self):
        self.g = {}

    def __iter__(self):
        return iter(self.g)

    def __getitem__(self, k):
        return self.g[k]

    def add_group(self, name, quota=1, surplus=False):
        self.g[name] = (quota, surplus)

    def calc_quota(self, farm):
        total = sum(x[0] for x in self.g.values())
        size = farm.count_cpus()
        new_g = {}
        for k, v in self.g.iteritems():
            new_g[k] = int(round((float(v[0]) / total) * size))
        return new_g

    def set_sibling(self, group, other):
        pass

    def __contains__(self, x):
        return x in self.g

    def __str__(self):
        return pprint.pformat(self.g)

