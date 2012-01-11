#!/usr/bin/env python

import sys, os
import glob
import api
from pprint import pprint

#dc = api.DirectoryCleaner(exclude_dirs=['exclude','scripts','spanprocessor','timecourses','ttest'])
#dc.remove('.err','.log','.REML_cmd','.tc','.HEAD','.BRIK')
#dc.move('.1D')


# initialize variable dictionary:
vars = {}

# determine if using cni or lucas:
data_type = 'cni'

# list the subjects to be processed:
exclude_dirs = ['exclude','scripts','spanprocessor','timecourses','ttest',\
                'dd083111','dk091611','ju083111','mm110111']
subjects = []
vars['subjects'] = subjects

# cni variables:
raw_anat = '0006_01_T1w_9mm_BRAVO.nii.gz'
raw_funcs = ['0004_01_BOLD_EPI_29mm_2sec.nii.gz','0005_01_BOLD_EPI_29mm_2sec.nii.gz']
raw_funcs_alternate = ['04_BOLD_EPI_29mm_2sec_1_0.nii.gz','05_BOLD_EPI_29mm_2sec_1_0.nii.gz']
func_names = ['pasreg','actreg']

# set standard variable defaults:
api.set_standard_defaults(vars)
api.set_regreg_defaults(vars)

# running from scripts directory?
run_from_scripts_dir = True

# scripts directory name (OPTIONAL):
scripts_dir = 'scripts'
vars['scripts_dir'] = scripts_dir

# change directory if neccessary:
if run_from_scripts_dir:
    os.chdir('../')


# load in variables:
if data_type == 'cni':
    if subjects:
        vars['subject_dirs'] = api.parse_dirs(prefixes=subjects)
    elif exclude_dirs:
        vars['subject_dirs'] = api.parse_dirs(exclude=exclude_dirs)
    vars['raw_funcs'] = raw_funcs
    vars['raw_funcs_alt'] = raw_funcs_alternate
    vars['raw_anat'] = raw_anat
    vars['func_names'] = func_names
    
    
    
    # reg reg vars:
    vars['reg_nifti_name'] = 'actreg_masked.nii'
    vars['reg_mask_name'] = 'talairach_mask.nii'
    vars['reg_resp_vec_name'] = 'ahalftrial.1D'
    vars['reg_onset_vec_name'] = 'achoosehalf.1D'
    vars['reg_response_tr'] = 3
    vars['reg_subjects'] = vars['subject_dirs']
    vars['reg_total_trials'] = 72
    vars['reg_prediction_tr_len'] = 3
    vars['lag'] = 2
    vars['reg_trial_trs'] = 3
    vars['reg_mask_dir'] = scripts_dir
    #vars['use_mask'] = False
    
# generate additional variables:

if data_type == 'cni':
    api.cni_find_trs_slices(vars)
    api.define_leadouts(vars)
    api.set_motion_labels(vars)
   
pprint(vars)

'''
for dir in vars['subject_dirs']:
    os.chdir(dir)
    SubProc = api.Preprocessor(data_type=data_type)
    SubProc.initialize_variables(vars)
    SubProc.run()
    os.chdir('../')
'''

RegReg = api.RegRegPipe()
RegReg.initialize_variables(vars)
RegReg.run()


#os.chdir('scripts')
#tempProc = api.Preprocessor(data_type=data_type)
#tempProc.initialize_variables(vars)
#tempProc.mask()

#pprint(vars)
#pprint(SubProc.__dict__)
