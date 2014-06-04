#!/usr/bin/python


class Group(object):
    """ A tree of scheduling groups. Leaf nodes are groups where jobs are
        actually submitted, mid-level nodes set limits on the surplus-sharing
        abilities of this tree of groups.
    """

    def __init__(self, name, quota=0, surplus=False):
        # These variables define the nature of the group, and are explicitly set
        self.name = name
        self.quota = quota
        self.parent = None
        self.accept_surplus = surplus
        self.children = {}

        # These values are calculated/derived during a run of the simulation
        self.norm_quota = None
        self.demand = 0
        self.usage = 0
        self.surplus = 0

    def add_child(self, name, quota=0, surplus=False):
        """ Add a child node to this one, setting it's parent pointer """

        new = Group(name, quota=quota, surplus=surplus)
        new.parent = self
        self.children[name] = new

    def set_character(self, num=0, cpu=1, mem=None, avg=3600, std=600):
        """ Sets the characteristic properties of jobs submitted into this
            group, such as number of cpus, average length, etc...
        """
        self.num = num
        self.cpu = cpu
        self.mem = mem if mem is not None else cpu * 2000
        self.avg = avg
        self.std = std

    def full_name(self):
        names = list()
        parent = self
        while parent is not None:
            names.append(parent.name)
            parent = parent.parent
        return ".".join(reversed(names))

    def walk(self):
        """ Recursively iterate through all lower nodes in the tree """
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
        return (x.name for x in self)

    def active_groups(self):
        """ Active groups are leaf nodes -- i.e. nodes with a quota """
        return (x for x in self if x.quota > 0)

    def __getitem__(self, key):
        return self.children[key]

    def update_quota(self, farm):
        """ Recalculate the actual quotas for each group, based on a farm of
            a given size.
        """
        total = sum(x.quota for x in self)
        size = farm.count_cpus()

        # First calculate quota for leaf nodes (groups with .quota > 0)
        for grp in self:
            # will be 0 for non-leaf nodes
            my_quota = int(round((float(grp.quota) / total) * size))
            grp.norm_quota = my_quota

        # Now set intermediate nodes to have quotas=sum of all children
        for grp in self:
            child_quotas = sum(x.norm_quota for x in grp)
            grp.norm_quota += child_quotas

    def update_surplus(self):
        """ Surplus is un-used slots by a groups children """
        for sub in self:
            sub.surplus = sum(x.norm_quota - x.usage for x in sub if x.quota > 0)

    def __repr__(self):
        return '<0x%x> %s (%d)' % (id(self), self.name, self.quota)

    def __iter__(self):
        return iter(self.walk())

    def __contains__(self, key):
        return (len([x.name for x in self if x.name == key]) > 0)

    def __str__(self):
        return '%s: surplus %s, quota %d, num %d' % \
               (self.name, self.accept_surplus, self.quota, self.num)


# For testing only...
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
