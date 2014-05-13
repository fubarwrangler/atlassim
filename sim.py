#!/usr/bin/python


import computefarm as bs
import stats as st

farm = bs.Farm()


groups = bs.Groups()
groups.add_group("prod", 2)
groups.add_group("short", 3)
groups.add_group("long", 2)
groups.add_group("mp8", 10)
groups.add_group("grid", 0.3)
groups.add_group("himem", 6)
st.make_groups(groups)

dist = (
    (24, 10),
    (32, 25),
    (8, 15),
)

farm.generate_from_dist(dist, size=20)

queue = bs.JobQueue()
queue.fill({"grid": 20, "prod": 40, "short": 114, "long": 61, "mp8": 13})
for x in queue.match_jobs({"group": "mp8"}):
    x.cpus = 8
    x.memory *= 6


farm.attach_groups(groups)
farm.attach_queue(queue)

#farm.set_negotiatior_rank(bs.breadth_first)
farm.negotiate_jobs()

for i in range(5000):
    farm.advance_time(1)
    if not i % 100:
        farm.negotiate_jobs()
        #print farm.queues[0]
    usage = farm.get_usage()
    for g in groups:
        st.push_data(g, usage[g])
    print st.get_data('long')


