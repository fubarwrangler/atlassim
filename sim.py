#!/usr/bin/python


import batchslots as bs

farm = bs.Farm()


dist = (
    (24, 60),
    (32, 25),
    (8, 15),
)

farm.generate_from_dist(dist, size=40)
print farm, "\n\n\n"

print "\n".join(map(str, farm.get_sorting(bs.largest_first)))
