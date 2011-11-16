#!/usr/bin/env python

import api
from pprint import pprint

KAI = api.PipeWrapper()
KAI.subjects = ['dh110111','kk102611','zw092811','ms101911']
KAI.data_type = 'cni'
KAI.func_names = ['actreg','pasreg']
KAI.anat_scan_num = 6
KAI.func_scan_nums = [4,5]

KAI.preprocess = True
KAI.threads = 4

pprint(KAI.vars)
KAI.run()
