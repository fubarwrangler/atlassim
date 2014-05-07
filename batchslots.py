#!/usr/bin/python

import sys
import random
import itertools
import pprint

import logging
from collections import defaultdict


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format="(%(levelname)5s) %(message)s")
log = logging.getLogger('')


IDLE = 0
RUNNING = 1
COMPLETED = 2


class BatchExcept(Exception):
    pass


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


class Machine(object):
    """ Class representing one machine in a compute cluster """

    _ids = itertools.count(0)

    def __init__(self, cpus=24, memory=None, name=None):

        self.name = name if name else "node%04d" % self._ids.next()

        self.cpus = cpus
        self.totalcpus = cpus
        self.memory = memory if memory is not None else 1000 * 2 * cpus
        self.totalmemory = self.memory
        self.num_jobs = 0.0

        self._jobs = list()

    def __iter__(self):
        return iter(self._jobs)

    def start_job(self, job):
        self.cpus -= job.cpus
        self.memory -= job.memory

        job.slotid = len(self._jobs)
        job.state = RUNNING
        job.current_node = self.name

        self._jobs.append(job)
        self.num_jobs += 1

    def end_job(self, job):
        self.cpus += job.cpus
        self.memory += job.memory
        self._jobs.remove(job)
        self.num_jobs -= 1

    def advance_time(self, step):
        for job in self._jobs:
            job.advance_time(step)
            if job.state == COMPLETED:
                log.debug("Job %s completed on %s", job, self)
                self.end_job(job)

    def __str__(self):

        return "%s (%d jobs) (%d/%d cpu) (%d/%d ram)" % \
               (self.name, len(self._jobs), self.cpus, self.totalcpus,
                self.memory, self.totalmemory)

    def long(self):
        s = "%s  (%d jobs) CPUs %2d (%2d) - RAM (%5d) %5d" % \
            (self.name, len(self._jobs), self.totalcpus - self.cpus, self.totalcpus,
             self.totalmemory - self.memory, self.totalmemory)
        if len(self._jobs) > 0:
            j = "\n    ".join(str(x) for x in self._jobs)
            return s + "\n    " + j
        else:
            return s


def depth_first(key):
    return -key.cpus


def largest_first(key):
    return key.totalcpus


def breadth_first(key):
    return key.cpus


class Farm(object):

    def __init__(self, ranking=depth_first):
        self._m = list()
        self.queues = list()
        self.groups = None
        self.set_negotiatior_rank(ranking)
        self.time = 0

    def __iter__(self):
        return iter(self._m)

    def count_cpus(self):
        return sum(x.totalcpus for x in self._m)

    def count_memory(self):
        return sum(x.totalmemory for x in self._m)

    def best_machines(self):
        return sorted(self._m, key=self._jobsorter)

    def set_negotiatior_rank(self, fn):
        """ Jobsorter functions need to return the best slot with the
            highest number
        """
        self._jobsorter = fn

    @staticmethod
    def slotweight(job):
        return job.cpus

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
        return "\n".join([x.long() for x in self])

    def print_usage(self):
        usage = defaultdict(int)
        for machine in self._m:
            for job in machine:
                usage[job.group] += self.slotweight(job)
        print usage

    def get_slots_fitting(self, job):

        return (x for x in self if x.cpus >= job.cpus and x.memory >= job.memory)

    def match_slots(self, query):

        def check_machine(machine, query):
            for k, v in query.iteritems():
                if getattr(machine, k) != v:
                    return False
            return True

        return (x for x in self if check_machine(x, query))

    def sort_by(self, sort_fn):
        return sorted(self, key=sort_fn)

    def attach_queue(self, q):
        self.queues.append(q)

    def attach_groups(self, g):
        assert (self.groups is None)
        self.groups = g

    def advance_time(self, step):
        for machine in self:
            machine.advance_time(step)
        self.time += step

    def sort_groups_by_usage(self):
        """ Return group and usage in negotiation order, least used to most. """

        assert (self.groups is not None)

        usage = defaultdict(int)
        for grp in self.groups:
            for queue in self.queues:
                jobs = queue.match_jobs({"group": grp, "state": RUNNING})
                usage[grp] += sum(self.slotweight(x) for x in jobs)
        return [(x, usage[x]) for x in sorted(usage, key=lambda x: usage[x])]

    def negotiate_jobs(self):

        for n, queue in enumerate(self.queues):
            log.info("Negotiate with queue %d - %d jobs", n + 1, len(queue))
            self._negotiate_queue(queue)

    def _negotiate_queue(self, queue):

        quotas = self.groups.calc_quota(self)
        log.debug("groups: %s" % quotas)

        for group, usage in self.sort_groups_by_usage():
            quota = quotas[group]
            log.info("Negotiate for %s: usage=%d quota=%d", group, usage, quota)
            for job in queue.match_jobs({"group": group, "state": IDLE}):
                candidate_weight = self.slotweight(job)

                if usage >= quota:
                    log.info("Group %s usage(%d) >= quota(%d), end",
                             group, usage, quota)
                    break
                elif usage + candidate_weight > quota:
                    log.debug("Job '%s' would put '%s' over quota", job, group)
                    continue

                matching = self.get_slots_fitting(job)

                try:
                    best = max(matching, key=self._jobsorter)
                except ValueError:
                    log.info("No slots found matching job %s", job)
                else:
                    log.info("Job '%s' matched to slot '%s'", job, best)
                    best.start_job(job)
                    usage += candidate_weight


class BatchJob(object):
    """ Class representing one job for the batch system """

    def __init__(self, cpus=1, memory=None, group="grid", length=None,
                 len_avg=None, len_splay=60):
        self.cpus = cpus
        self.memory = memory if memory is not None else cpus * 2000
        self.group = group

        if length is not None:
            self.length = length
        elif len_avg is not None:
            self.length = len_avg + 2 * (random.random() * len_splay) - len_splay
        elif length is None and len_avg is None:
            self.length = random.random() * 200 + 3500
        else:
            raise AttributeError("length or len_avg must be defined, not both")

        self.current_node = None
        self.slotid = None
        self.state = IDLE
        self.runtime = 0
        self.queue = None

    def advance_time(self, step):
        self.runtime += step
        if self.runtime >= self.length:
            self.state = COMPLETED
            #self.queue.remove(self)

    def state_char(self):
        return ['I', 'R', 'C'][self.state]

    def __str__(self):
        x = "%s: %d CPU %d Mb" % (self.group, self.cpus, self.memory)
        if self.state == RUNNING:
            x = "slot%d " % self.slotid + x
        return x

    def long(self):
        s = "%2d-core  %5dMb  %10s   %s" % (self.cpus, self.memory, self.group,
                                            self.state_char())
        if self.current_node and self.slotid is not None:
            s += "   (%s@%s)" % (self.slotid, self.current_node)
        return s


class JobQueue(object):

    def __init__(self):
        self._q = list()

    def add_job(self, jobobj):
        jobobj.queue = self._q
        self._q.append(jobobj)

    def fill(self, group_count):
        for grp, cnt in group_count.iteritems():
            for x in xrange(cnt):
                self.add_job(BatchJob(group=grp))

    def __getitem__(self, n):
        return self._q[n]

    def __str__(self):
        return "\n".join([x.long() for x in self._q])

    def match_jobs(self, query):

        def check_job(job, query):
            for k, v in query.iteritems():
                if getattr(job, k) != v:
                    return False
            return True

        return (x for x in self if check_job(x, query))

    def __len__(self):
        return len(self._q)

    def __iter__(self):
        return iter(self._q)
