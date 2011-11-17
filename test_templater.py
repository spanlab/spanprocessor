#!/usr/bin/env python

import api
from pprint import pprint

robot = api.PipeWrapper()
robot.subjects = []
robot.exclude_dirs = ['dh110111']
robot.data_type = 'cni'
robot.func_names = ['actgive','pasgive']
robot.anat_scan_num = 6
robot.func_scan_nums = [[1,2],[4,6]]

robot.ttest = True



robot.vars['leadin'] = 0
robot.vars['leadout'] = 0

robot.threads = 1
robot.run()