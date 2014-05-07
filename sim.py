#!/usr/bin/python


import computefarm as bs

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

farm.generate_from_dist(dist, size=200)

queue1 = bs.JobQueue()
queue1.fill({"grid": 2, "prod": 40, "short": 114, "long": 61})

queue2 = bs.JobQueue()
queue2.fill({"grid": 50, "mp8": 60, "prod": 14, "long": 23})
for x in queue2.match_jobs({"group": "mp8"}):
    x.cpus = 8
    x.memory *= 6


farm.attach_groups(groups)
farm.attach_queue(queue1)
farm.attach_queue(queue2)

#farm.set_negotiatior_rank(bs.breadth_first)
farm.negotiate_jobs()

for i in range(10000):
    farm.advance_time(1)
    if not i % 100:
        farm.negotiate_jobs()
    #farm.print_usage()
