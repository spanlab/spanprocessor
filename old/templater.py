#!/usr/bin/env python

import api
from pprint import pprint

KAI = api.PipeWrapper()
KAI.subjects = ['dh110111']
KAI.data_type = 'cni'
KAI.func_names = ['actreg','pasreg']
KAI.anat_scan_num = 6
KAI.func_scan_nums = [4,5]

KAI.preprocess = True

KAI.do_anat_reconstruction = True
KAI.do_func_reconstruction = True
KAI.do_warp_anatomical = True
KAI.do_correct_motion = True
KAI.do_normalize = True
KAI.do_highpass_filter = False
KAI.do_warp_functionals = False
KAI.do_mask_functionals = False
KAI.do_convert_to_nifti = False

KAI.threads = 1
pprint(KAI.vars)
KAI.run()
