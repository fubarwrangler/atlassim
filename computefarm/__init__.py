#!/usr/bin/python

import sys
import logging

__all__ = ['IDLE', 'RUNNING', 'COMPLETED', 'BatchExcept',
           'Farm', 'Group', 'BatchJob', 'Machine', 'JobQueue']


logging.basicConfig(stream=sys.stdout, level=logging.DEBUG,
                    format="(%(levelname)5s) %(message)s")


IDLE = 0
RUNNING = 1
COMPLETED = 2


class BatchExcept(Exception):
    pass

from farm import Farm
from groups import Group
from job import BatchJob
from machine import Machine
from queue import JobQueue
