#!/usr/bin/python

import computefarm as bs
import stats as st

import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.animation as animation

farm = bs.Farm()

groups = bs.Group('')
groups.add_child("atlas")
groups.add_child("grid", 0.3)
groups['atlas'].add_child('production')
groups['atlas'].add_child('analysis')
groups['atlas']['production'].add_child('prod', 6)
groups['atlas']['production'].add_child('mp8', 9)
groups['atlas']['analysis'].add_child('short', 7)
groups['atlas']['analysis'].add_child('long', 5)
st.make_groups(groups, 2600)

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

for i in range(10000):
    farm.advance_time(1)
    if not i % 100:
        farm.negotiate_jobs()
        #print farm.queues[0]
    if not i % 6:
        usage = farm.get_usage()
        for g in (x.name for x in groups.active_groups()):
            st.push_data(g, usage[g])
        #print st.get_data('long')

#print np.vstack((x[1] for x in st.get_groups()))
#print [x[1] for x in st.get_groups()]

plt.stackplot(np.arange(st.get_size()), np.vstack((x[1] for x in st.get_groups())),
              colors=('#00FF00', '#FF0000', '#E3CF57', '#0000FF', '#FF00FF', '#00FFFF',
                      '#FFFF00', '#FFC0CB', '#C67171', '#000000'))
plt.show()
