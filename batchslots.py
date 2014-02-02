#!/usr/bin/python

import os
import random
import itertools


IDLE = 0
RUNNING = 1
COMPLETED = 2

class BatchExcept(Exception):
    pass

groups = {
    "prod": 30, "mp8": 10, "short": 6,
    "long": 6, "himem": 8, "grid": 0.4
}


def set_quotas(farm):
    global groups
    new_g = {}
    total = sum(groups.values())
    size = farm.count_cpus()
    for k, v in groups.iteritems():
        new_g[k] = int(round((float(v) / total) * size))
    groups = new_g

siblings = [["short", "long"], ["prod", "mp8", "himem"], ["grid"]]


def get_siblings(group):
    if group not in groups:
        raise BatchExcept("Group %s not in groups" % group)
    for lst in siblings:
        if group in lst:
            return [x for x in lst if x != group]
    return []


class Machine(object):
    """ Class representing one machine in a compute cluster """

    _ids = itertools.count(0)

    def __init__(self, cpus=24, memory=None, name=None):

        self.name = name if name else "node%04d" % self._ids.next()

        self.cpus = cpus
        self.totalcpus = cpus
        self.memory = memory if memory is not None else 1000 * 2 * cpus
        self.totalmemory = self.memory

        self._jobs = list()

    def start_job(self, job):
        self.cpus -= job.cpus
        self.memory -= job.memory

        job.slotid = len(self._jobs)
        job.state = RUNNING
        job.current_node = self.name

        self._jobs.append(job)

    def __str__(self):
        s = "%s  (%d jobs) CPUs %2d (%2d) - RAM (%5d) %5d" % \
            (self.name, len(self._jobs), self.totalcpus, self.cpus,
             self.totalmemory, self.memory)
        if len(self._jobs) > 0:
            j = "\n    ".join(str(x) for x in self._jobs)
            return s + "\n    " + j
        else:
            return s

def depth_first(key):
    return key.cpus

def largest_first(key):
    return -key.totalcpus


class Farm(object):

    def __init__(self):
        self._m = list()
        self._jobsorter = depth_first

    def count_cpus(self):
        return sum(x.totalcpus for x in self._m)

    def count_memory(self):
        return sum(x.totalmemory for x in self._m)

    def generate_from_dist(self, cpuweights, size=None):
        """ @cpuweights is a list of tuples, the first element of which is
            the number of cpus and the second is a weight or a count

            if @size is None (default), the second element of the items in
            @cpuweights is an absolute count of how many n-core machines to
            create, if size is a number, the same element is a weight that gets
            normalized to make the total = size
        """

        if not size:
            for cpus, count in cpuweights:
                for n in xrange(count):
                    self._m.append(Machine(cpus=cpus))
        else:
            total = sum(x[1] for x in cpuweights)
            for cpus, count in cpuweights:
                for x in xrange(int(size * (count / float(total)))):
                    self._m.append(Machine(cpus=cpus))

    def __str__(self):
        return "\n".join(map(str, self._m))

    def get_slots_matching(self, req_cpu, req_memory):

        def match(machine, cpu, ram):
            return (machine.cpus >= cpu and machine.memory >= ram)

        return [x for x in self._m if match(x, req_cpu, req_memory)]

    def sort_by(self, sort_fn):
        return sorted(self._m, key=sort_fn)

    def negotiate_jobs(self, queue):

        for job in (x for x in queue if x.state == IDLE):
            pass


class BatchJob(object):
    """ Class representing one job for the batch system """

    def __init__(self, cpus=1, memory=None, group="grid", length=None):
        self.cpus = cpus
        self.memory = memory if memory is not None else cpus * 2000
        if group not in groups:
            raise BatchExcept("Group %s not found" % group)
        self.group = group

        # default is about an hour
        self.length = length if length is not None else random.randint(3500, 3700)

        self.current_node = None
        self.slotid = None
        self.state = IDLE

    @staticmethod
    def state_name(state):
        return ['I', 'R', 'C'][state]

    def __str__(self):
        s = "%2d-core  %5dMb  %10s   %s" % (self.cpus, self.memory, self.group,
                                            self.state_name(self.state))
        if self.current_node and self.slotid is not None:
            s += "   (%s@%s)" % (self.slotid, self.current_node)
        return s


class JobQueue(object):

    def __init__(self):
        self._q = list()

    def add_job(self, jobobj):
        self._q.append(jobobj)

    def fill(self, group_count):
        for grp, cnt in group_count.iteritems():
            for x in xrange(cnt):
                self.add_job(BatchJob(group=grp))

    def __getitem__(self, n):
        return self._q[n]

    def __str__(self):
        return "\n".join(map(str, self._q))

    def match_jobs(self, query):
        conditions = []

        def check_job(job, query):
            for k, v in query.iteritems():
                if getattr(job, k) != v:
                    return False
            return True

        return (x for x in self._q if check_job(x, query))


    def __iter__(self):
        return iter(self._q)
