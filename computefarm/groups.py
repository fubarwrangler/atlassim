#!/usr/bin/python

import pprint


class Group(object):

    def __init__(self, name, quota=0, surplus=False):
        self.name = name
        self.quota = quota
        self.parent = None
        self.surplus = surplus
        self.children = {}
        self.norm_quota = None
        self.demand = 0

    def add_child(self, name, quota=0, surplus=False):
        new = Group(name, quota=quota, surplus=surplus)
        new.parent = self
        self.children[name] = new

    def set_character(self, num=0, cpu=1, mem=None, avg=3600, std=600):
        self.num = num
        self.cpu = cpu
        self.mem = mem if mem is not None else cpu * 2000
        self.avg = avg
        self.std = std

    def walk(self):
        if not self.children:
            return
        for x in self.children.values():
            yield x
            for y in x.walk():
                yield y

    def get_by_name(self, name):
        if self.name == name:
            return self
        for x in self.walk():
            if name == x.name:
                return x
        raise Exception("No group %s found" % name)

    def names(self):
        return (x.name for x in self.walk())

    def active_groups(self):
        return (x for x in self.walk() if x.quota > 0)

    def sum_child_quotas(self):
        return sum(x.quota for x in self.walk())

    def __getitem__(self, key):
        return self.children[key]

    def calc_quota(self, farm):
        total = self.sum_child_quotas()
        size = farm.count_cpus()
        new_g = {}
        for grp in self.walk():
            normed = int(round((float(grp.quota) / total) * size))
            new_g[grp.name] = normed
            grp.norm_quota = normed
        return new_g

    def __repr__(self):
        return '<0x%x> %s (%d)' % (id(self), self.name, self.quota)

    def __iter__(self):
        return iter(self.walk())

    def __contains__(self, key):
        return (len([x.name for x in self.walk() if x.name == key]) > 0)

    def __str__(self):
        return '%s: surplus %s, quota %d, num %d' % (self.name, self.surplus, self.quota, self.num)


if __name__ == '__main__':
    root = Group('<>')
    root.add_child('atlas')
    root['atlas'].add_child('analysis')
    root['atlas'].add_child('production')
    root['atlas']['analysis'].add_child('short', 20)
    root['atlas']['analysis'].add_child('long', 10)
    root['atlas']['production'].add_child('mp8', 65)
    root['atlas']['production'].add_child('prod', 100)
    root.add_child('grid', 40)
