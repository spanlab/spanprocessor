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
#exclude_dirs = ['exclude','scripts','spanprocessor','timecourses','ttest',\
#                'dd083111','dk091611','ju083111','mm110111']
#subjects = ['ag120605','cw112205','db110905f','db111605c','dw100605c',
#            'dw101205f','eh111005c','eh112905f','et081905c','et090105f',
#            'hh011006','jd011006','jh110105f','jh111705c','kp082205c',
#            'kp083105f','mc100605c','mc101205f']

subjects = ['jh111705c','jh112205','kp082205c','kp083105f',
            'rc112905','cw112205','db110905f','se090105c','db111605c',
            'mc100605c','se090605f','mc101205f','sn020806','ds090605f',
            'dw100605c','mh100605f','st110305c','dw101205f','mh101205c',
            'st110805f','eh111005c','mm020606','eh112905f','tf120805f',
            'et081905c','tf121505c','et090105f','tv080707','hh011006',
            'nb081005f','we081905f','nb081705c','we083105c','nc081005f',
            'wh100405c','nc081705c','wh101005f','jd011006','nd020806',
            'jh110105f','ng120605']


vars['subjects'] = subjects

# cni variables:
#raw_anat = '0006_01_T1w_9mm_BRAVO.nii.gz'
#raw_funcs = ['0004_01_BOLD_EPI_29mm_2sec.nii.gz','0005_01_BOLD_EPI_29mm_2sec.nii.gz']
#raw_funcs_alternate = ['04_BOLD_EPI_29mm_2sec_1_0.nii.gz','05_BOLD_EPI_29mm_2sec_1_0.nii.gz']
#func_names = ['pasreg','actreg']

# set standard variable defaults:
api.set_standard_defaults(vars)
#api.set_regreg_defaults(vars)

# running from scripts directory?
run_from_scripts_dir = True

# scripts directory name (OPTIONAL):
scripts_dir = 'reg_output'
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
    #vars['raw_funcs'] = raw_funcs
    #vars['raw_funcs_alt'] = raw_funcs_alternate
    #vars['raw_anat'] = raw_anat
    #vars['func_names'] = func_names
    
    vars['talairach_dxyz'] = 3.75
    vars['dynamic_iti'] = False
    
    
    # reg reg vars:
    # should only use either of the two bounds, for the other use the
    # lagrange.
    vars['lambda1'] = 68.
    # higher bound 1 -> more coefficients 
    vars['bound1'] = 1.0
    # higher lambda 2 -> more smoothness
    vars['lambda2'] = 1000.0
    vars['lambda3'] = 100.
    vars['bound3'] = 1.0e0
    vars['inv_step'] = 1500000.
    vars['set_tol'] = 1e-07
    vars['max_its'] = 1000
    vars['lookback'] = False
    vars['lookback_trs'] = 0
    vars['use_mask'] = True
    vars['reg_nifti_name'] = ['pop12_warp375.nii','pop34_warp375.nii']
    vars['reg_mask_name'] = 'talairach_mask375.nii'
    vars['reg_resp_vec_name'] = ['choice12.1D','choice34.1D']
    vars['reg_onset_vec_name'] = 'trialonsets.1D'
    vars['reg_response_tr'] = 7
    vars['reg_subjects'] = vars['subject_dirs']
    vars['reg_total_trials'] = 40
    vars['reg_prediction_tr_len'] = 5
    vars['lag'] = 2
    vars['reg_trial_trs'] = 7
    vars['reg_mask_dir'] = scripts_dir
    #vars['use_mask'] = False
    
# generate additional variables:

#if data_type == 'cni':
#    api.cni_find_trs_slices(vars)
#    api.define_leadouts(vars)
#    api.set_motion_labels(vars)
   
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
