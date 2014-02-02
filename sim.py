#!/usr/bin/python


import batchslots as bs

farm = bs.Farm()


dist = (
    (24, 60),
    (32, 25),
    (8, 15),
)

farm.generate_from_dist(dist, size=40)
bs.set_quotas(farm)


queue = bs.JobQueue()
queue.fill({"grid": 2, "prod": 40, "short": 14})
queue[4].state = bs.RUNNING
print "\n".join(map(str, queue.match_jobs({"group": "prod", "state": bs.RUNNING})))
