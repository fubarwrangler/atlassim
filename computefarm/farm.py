#!/usr/bin/python

import logging
from collections import defaultdict

from computefarm import RUNNING, IDLE
from machine import Machine

log = logging.getLogger('sim')

largest_first = lambda key: key.totalcpus
breadth_first = lambda key: key.cpus
depth_first = lambda key: -key.cpus

# Used internally in negotiation
END_CYCLE = False
NOT_ALLOWED = None


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
        for x in usage:
            self.groups.get_by_name(x).usage = usage[x]

        for group in self.groups:
            if group.children:
                group.usage = sum(x.usage for x in group.children.values())

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
        """ Return group and usage in "starvation" order, least used to most. """

        usage = defaultdict(int)
        for grp in self.groups.active_groups():
            jobs = self.queue.match_jobs({"group": grp.name, "state": RUNNING})
            used = sum(self.slotweight(x) for x in jobs)
            usage[grp.name] += used
            #grp.usage = used
        return [(x, usage[x]) for x in sorted(usage, key=lambda x: usage[x])]

    def allowed_run(self, job, group, demand):
        quota = group.norm_quota
        usage = group.usage
        name = group.name

        candidate_weight = self.slotweight(job)
        seek_surplus = False

        go = 'try for surplus...' if group.accept_surplus else 'end.'
        if usage >= quota:
            log.info("Group %s usage(%d) >= quota(%d), %s",
                     name, usage, quota, go)
            if not group.accept_surplus:
                return END_CYCLE
            else:
                seek_surplus = True
        elif candidate_weight + usage > quota:
            log.debug("Job '%s' would put '%s' over quota, %s", job, name, go)
            if not group.accept_surplus:
                return NOT_ALLOWED
            else:
                seek_surplus = True

        if seek_surplus:
            group.parent.update_surplus()
            self.print_groups()
            avail_surplus = 0
            parent = group.parent
            while parent:
                surplus = min(demand, parent.surplus)
                log.info("Group %s allocated %d surplus from %s",
                         name, surplus, parent.name)
                avail_surplus += surplus
                #parent.surplus -= surplus
                parent = parent.parent
                if not parent.accept_surplus:
                    break
            if avail_surplus:
                quota += avail_surplus
                log.info("Surplus was found for %s (%d), quota now %d",
                         name, avail_surplus, quota)
            else:
                log.info("No surplus available for %s, end.", name)
                return END_CYCLE

            if candidate_weight + usage > quota:
                log.info('Surplus was not sufficient for job, not matching')
                return NOT_ALLOWED

        parent_ok = self.violate_parent_quota(group, candidate_weight)
        if parent_ok is END_CYCLE or parent_ok is NOT_ALLOWED:
            return parent_ok

        return candidate_weight

    @staticmethod
    def violate_parent_quota(group, weight):
        while group.parent:
            if group.usage >= group.norm_quota:
                log.info("Group %s at quota %d (usage=%d)", group.full_name(),
                         group.norm_quota, group.usage)
                return END_CYCLE
            if group.usage + weight > group.norm_quota:
                log.info("Weight of %d would put group %s over quota %d (usage=%d)",
                         weight, group.full_name(), group.norm_quota, group.usage)
                return NOT_ALLOWED
            group = group.parent
        return weight

    def negotiate_jobs(self):

        log.info("Negotiate with %d jobs", len(self.queue))
        self.groups.update_quota(self)
        self.groups.update_surplus()
        self.get_usage()

        for group in self.groups:
            jobs = self.queue.match_jobs({"group": group.name, "state": IDLE})
            group.demand = sum(self.slotweight(x) for x in jobs)

        self.print_groups()

        for name, usage in self.sort_groups_by_usage():
            group = self.groups.get_by_name(name)
            quota = group.norm_quota
            demand = group.demand

            log.info("Negotiate for %s: usage=%d quota=%d demand=%d", name, usage, quota, demand)
            for job in self.queue.match_jobs({"group": name, "state": IDLE}):

                weight = self.allowed_run(job, group, demand)

                if weight is END_CYCLE:
                    break
                elif weight is NOT_ALLOWED:
                    continue

                matching = self.get_slots_fitting(job)

                try:
                    best = max(matching, key=self._jobsorter)
                except ValueError:
                    log.info("No slots found matching job %s", job)
                else:
                    log.info("Job '%s' matched to slot '%s'", job, best)
                    best.start_job(job)
                    group.usage += weight
                    parent = group.parent
                    while parent:
                        parent.usage += weight
                        parent.surplus -= weight
                        parent = parent.parent

    def print_groups(self):
        for x in self.groups:
            log.info("%s: usage=%d quota=%d(%d) demand=%d surplus=%d", x.full_name(),
                     x.usage, x.norm_quota, x.quota, x.demand, x.surplus)

