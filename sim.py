#!/usr/bin/python


import batchslots as bs

n = bs.FarmNode("node01", cpus=24)
j = bs.BatchJob(group="prod")
k = bs.BatchJob(group="mp8", cpus=3)


print n
print j

n.start_job(k)
n.start_job(j)

print n

print k