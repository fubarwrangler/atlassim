#!/usr/bin/python

import logging
from collections import defaultdict

from computefarm import RUNNING, IDLE
from machine import Machine

log = logging.getLogger('sim')


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
        log.info("Added %d machines to farm", len(self._m))

    def __str__(self):
        return "\n".join([x.long() for x in self])

    def get_usage(self):
        usage = defaultdict(int)

        for machine in self._m:
            for job in machine:
                usage[job.group] += self.slotweight(job)

        return usage

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
        self.queue = q

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
        for grp in (x.name for x in self.groups.active_groups()):
            jobs = self.queue.match_jobs({"group": grp, "state": RUNNING})
            usage[grp] += sum(self.slotweight(x) for x in jobs)
        return [(x, usage[x]) for x in sorted(usage, key=lambda x: usage[x])]

    def negotiate_jobs(self):

        log.info("Negotiate with queue -- %d jobs", len(self.queue))
        quotas = self.groups.calc_quota(self)
        #surplus = self.calc_surplus(self.groups, )

        for group, usage in self.sort_groups_by_usage():
            quota = quotas[group]
            log.info("Negotiate for %s: usage=%d quota=%d", group, usage, quota)
            for job in self.queue.match_jobs({"group": group, "state": IDLE}):
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
