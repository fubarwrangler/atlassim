#!/usr/bin/python


import batchslots as bs

farm = bs.Farm()


groups = bs.Groups()
groups.add_group("prod", 2)
groups.add_group("short", 3)
groups.add_group("long", 2)
groups.add_group("mp8", 10)
groups.add_group("grid", 0.3)
groups.add_group("himem", 6)

dist = (
    (24, 10),
    (32, 25),
    (8, 15),
)

farm.generate_from_dist(dist, size=20)

queue = bs.JobQueue()
queue.fill({"grid": 2, "prod": 40, "short": 114, "long": 61})


farm.attach_queue(queue)
farm.attach_groups(groups)
# queue[4].state=bs.RUNNING
# queue[3].state=bs.RUNNING
# queue[2].state=bs.RUNNING
# queue[49].state=bs.RUNNING
# for x in queue.match_jobs({"group": "grid"}):
#     x.state=bs.RUNNING
farm.set_negotiatior_rank(bs.depth_first)
farm.negotiate_jobs()

print farm
print farm.sort_groups_by_usage()