#!/usr/bin/python


import batchslots as bs

farm = bs.Farm()


dist = (
    (24, 60),
    (32, 25),
    (8, 15),
)

farm.generate_from_dist(dist, size=40)

queue = bs.JobQueue()
queue.fill({"grid": 2, "prod": 40, "short": 14})

farm.attach_queue(queue)

# queue[4].state=bs.RUNNING
# queue[3].state=bs.RUNNING
# queue[2].state=bs.RUNNING
# queue[49].state=bs.RUNNING
# for x in queue.match_jobs({"group": "grid"}):
#     x.state=bs.RUNNING

print [str(x) for x in bs.groups.sort_usage(farm)]

