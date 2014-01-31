#!/usr/bin/python


import batchslots as bs

farm = bs.Farm()


dist = (
    (24, 60),
    (32, 25),
    (8, 15),
)

farm.generate_from_dist(dist, size=30)

print farm