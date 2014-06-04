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
    """
    """

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

    def set_negotiatior_rank(self, fn):
        """ Jobsorter functions need to return the best slot with the
            highest number
        """
        self._jobsorter = fn

    @staticmethod
    def slotweight(job):
        """ We define slotweight just as CPUs, no matter the memory usage """
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
        """ Update each group's usage by counting running jobs on the farm,
            each non-leaf group has it's usage set by summing it's children
        """
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
        """ Return all machines where this job could fit """

        return (x for x in self if x.cpus >= job.cpus and x.memory >= job.memory)

    # TODO: not needed?
    def match_slots(self, query):

        def check_machine(machine, query):
            for k, v in query.iteritems():
                if getattr(machine, k) != v:
                    return False
            return True

        return (x for x in self if check_machine(x, query))

    # TODO: not needed?
    def sort_by(self, sort_fn):
        return sorted(self, key=sort_fn)

    def attach_queue(self, q):
        self.queue = q

    def attach_groups(self, g):
        assert (self.groups is None)
        self.groups = g

    def advance_time(self, step):
        """ Advance time for each machine running a job, which in turn advances
            time for each job on that machine
        """
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
        return [(x, usage[x]) for x in sorted(usage, key=lambda x: usage[x])]

    def allowed_run(self, job, group, demand):
        """ Determine if a job is able to run in its group, accounting for quota
            usage and searchin for surplus from parent groups if available and
            accept_surplus is set.
        """

        quota = group.norm_quota
        usage = group.usage
        name = group.name

        candidate_weight = self.slotweight(job)
        seek_surplus = False

        go = 'try for surplus...' if group.accept_surplus else 'end.'

        # If job is over its usage...
        if usage >= quota:
            log.info("Group %s usage(%d) >= quota(%d), %s",
                     name, usage, quota, go)
            # ...and accept surplus is not set, end, otherwise set surplus flag
            if not group.accept_surplus:
                return END_CYCLE
            else:
                seek_surplus = True
        # Or if a job would put it's group over its quota...
        elif candidate_weight + usage > quota:
            log.debug("Job '%s' would put '%s' over quota, %s", job, name, go)

            # ...and accept surplus is not set, reject, otherwise set surplus flag
            if not group.accept_surplus:
                return NOT_ALLOWED
            else:
                seek_surplus = True

        if seek_surplus:
            self.print_groups()
            avail_surplus = 0

            # Walk up tree of parents gathering surplus until the root is hit
            parent = group.parent
            while parent:
                surplus = max(min(demand - avail_surplus, parent.surplus), 0)
                log.info("Group %s allocated %d surplus from %s",
                         name, surplus, parent.full_name())
                avail_surplus += surplus

                # We hit the root of the tree
                if not parent.parent:
                    log.info("Group %s no longer any surplus available", parent.full_name())
                    break

                # Parent doesn't accept surplus
                if not parent.accept_surplus:
                    log.info("Group %s no longer accepts surplus", parent.full_name())
                    break

                parent = parent.parent

            # If surplus found allocate it and set the quota to the higher value
            if avail_surplus:
                group.norm_quota += avail_surplus
                quota = group.norm_quota
                log.info("Surplus was found for %s (%d), quota now %d",
                         name, avail_surplus, group.norm_quota)
            else:
                log.info("No surplus available for %s, end.", name)
                return END_CYCLE

            if candidate_weight + usage > quota:
                log.info('Surplus was not sufficient for job, not matching')
                return NOT_ALLOWED

        # If the group would violate the quota of its group or any of its
        # parent's (already adjusted if needed for surplus counting)
        violate_quota = self.violate_parent_quota(group, candidate_weight)
        if violate_quota is END_CYCLE or violate_quota is NOT_ALLOWED:
            return violate_quota

        return candidate_weight

    @staticmethod
    def violate_parent_quota(group, weight):
        """ Again walk up the tree of parents and see if the quota is violated
            by a candidate job
        """
        while group.parent:
            if group.usage >= group.norm_quota and not group.accept_surplus:
                log.info("Group %s at quota %d (usage=%d)", group.full_name(),
                         group.norm_quota, group.usage)
                return END_CYCLE
            if group.usage + weight > group.norm_quota and not group.accept_surplus:
                log.info("Weight of %d would put group %s over quota %d (usage=%d)",
                         weight, group.full_name(), group.norm_quota, group.usage)
                return NOT_ALLOWED
            group = group.parent
        return weight

    def negotiate_jobs(self):
        """ Iterate over idle jobs and see if there are any matches for them """

        log.info("=" * 85)
        log.info("Negotiate with %d jobs", len([x for x in self.queue if x.state == IDLE]))

        # Recalculate actual quotas if they've been adjusted by the user
        self.groups.update_quota(self)
        # Update the usage of each group
        self.get_usage()

        for group in self.groups:
            jobs = self.queue.match_jobs({"group": group.name, "state": IDLE})

            # Demand is number of idle jobs in the queue
            group.demand = sum(self.slotweight(x) for x in jobs)

            # If the quota appears to be exceeded but accept_surplus is set,
            # make the new quota higher (set equal to usage) so if more surplus
            # is allocated things are counted correctly
            if group.usage > group.norm_quota and group.accept_surplus:
                group.norm_quota = group.usage

        self.print_groups()

        # For each group in correct order...
        for name, usage in self.sort_groups_by_usage():
            group = self.groups.get_by_name(name)
            quota = group.norm_quota
            demand = group.demand
            self.groups.update_surplus()

            if demand == 0:
                log.info("No jobs for group %s, skip negotiating", name)
                continue

            log.info("Negotiate for %s: usage=%d quota=%d demand=%d", name, usage, quota, demand)
            self.print_groups()

            # For each candidate idle-job in that group...
            for job in self.queue.match_jobs({"group": name, "state": IDLE}):

                # See if the job is allowed to run...
                weight = self.allowed_run(job, group, demand)

                # If the answer is neither of the following, then try to run it...
                if weight is END_CYCLE:
                    log.info("Done negotiating for group %s", name)
                    break
                elif weight is NOT_ALLOWED:
                    continue

                # Of all slots where job could fit...
                matching = self.get_slots_fitting(job)

                # ...find the one with the best rank
                try:
                    best = max(matching, key=self._jobsorter)
                except ValueError:
                    log.info("No slots found matching job %s", job)
                else:
                    log.info("Matched job '%s' to slot '%s'", job, best)

                    # State the job
                    best.start_job(job)

                    # Update the usage / surplus of the group and all parents up the tree
                    group.usage += weight
                    parent = group.parent
                    while parent:
                        parent.usage += weight
                        parent.surplus -= weight
                        parent = parent.parent
            else:
                log.info("No more jobs submitted for group %s", name)

    def print_groups(self):
        for x in self.groups:
            log.info("%s: usage=%d quota=%d(%d) demand=%d surplus=%d", x.full_name(),
                     x.usage, x.norm_quota, x.quota, x.demand, x.surplus)

