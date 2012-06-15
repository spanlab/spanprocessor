#!/usr/bin/env python

import sys, os
import glob
import api
from RegRegPipe_n import RegRegPipe, RRData
from pprint import pprint
from MiniGridsearch import MiniGridsearch as MG
import profile

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


# TOOK OUT wh101005c, no completed data
# RENAMED choice12.1D to _choice12.1D for ng120605, cause no pop12 data file!
subjects = ['jh111705c','jh112205','kp082205c','kp083105f',
            'rc112905','cw112205','db110905f','se090105c','db111605c',
            'mc100605c','se090605f','mc101205f','sn020806','ds090605f',
            'dw100605c','mh100605f','st110305c','dw101205f','mh101205c',
            'st110805f','eh111005c','mm020606','eh112905f','tf120805f',
            'et081905c','tf121505c','et090105f','tv080707','hh011006',
            'nb081005f','we081905f','nb081705c','we083105c','nc081005f',
            'wh100405f','nc081705c','jd011006','nd020806',
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






# load in variables:
if data_type == 'cni':
    if subjects:
        os.chdir('..')
        vars['subject_dirs'] = api.parse_dirs(prefixes=subjects)
        os.chdir('spanprocessor')
        print vars['subject_dirs']
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
    #vars['lambda1'] = 68.
    # higher bound 1 -> more coefficients 
    vars['bound1'] = 2.
    vars['bound2'] = 1.
    vars['bound3'] = 31.
    # higher lambda 2 -> more smoothness
    #vars['lambda2'] = 1000.0
    vars['lambda3'] = 1000.
    vars['inv_step'] = 1500000.
    vars['set_tol'] = 1e-04
    vars['max_its'] = 1000
    vars['lookback'] = False
    vars['lookback_trs'] = 0
    vars['use_mask'] = True
    vars['reg_nifti_name'] = ['pop12_warp375.nii','pop34_warp375.nii']
    vars['reg_mask_name'] = 'talairach_mask375.nii'
    vars['reg_resp_vec_name'] = ['choice12.1D','choice34.1D']
    vars['reg_onset_vec_name'] = 'trialonsets.1D'
    vars['reg_response_tr'] = 7
    vars['trs_of_interest'] = [1,2,3,4,5] 
    vars['reg_subjects'] = vars['subject_dirs']
    vars['reg_total_trials'] = 40
    vars['reg_prediction_tr_len'] = 5
    vars['lag'] = 2
    vars['reg_trial_trs'] = 7

    
    vars['random_seed'] = 217189111
    vars['warm_start'] = True
    vars['crossvalidation_folds'] = 1
    # type either trial or subject:
    vars['crossvalidation_type'] = 'subject'
    vars['downsample_type'] = 'subject'
    vars['with_replacement'] = True
    
    vars['loss'] = 'quadratic'
    vars['penalties'] = ['sparsity_bound', 'graphnet_bound_smooth', 'ridge_bound_smooth','graphnet']
    
    vars['output_filename'] = 'v2_%s_%s_%s_%s' % (str(vars['bound1']),
                                                 str(vars['bound2']),
                                                 str(vars['bound3']),
                                                 str(vars['lambda3']))
    
    
    vars['reg_mask_dir'] = 'reg_output'
    vars['reg_save_dir'] = 'reg_output'
    
    vars['top_dir'] = os.path.split(os.getcwd())[0]
    # scripts directory name (OPTIONAL):
    vars['scripts_dir'] = os.path.join(vars['top_dir'], 'spanprocessor')
    vars['save_dir'] = os.path.join(vars['top_dir'], 'reg_output')
    vars['reg_mask_dir'] = os.path.join(vars['top_dir'], 'reg_output')
    vars['bin_dir'] = os.path.join(vars['save_dir'], 'reg_bin')
    vars['records_dir'] = os.path.join(vars['save_dir'], 'records')
    vars['memmap_name'] = 'raw_data.npy'
    vars['sparse_matrix_name'] = 'sparse_matrix.mat'
    vars['affine_name'] = 'raw_affine.npy'
    
# generate additional variables:

#if data_type == 'cni':
#    api.cni_find_trs_slices(vars)
#    api.define_leadouts(vars)
#    api.set_motion_labels(vars)
   
   
#vars['reg_resp_vec_name'] = 'achoosepos.1D'
#vars['reg_onset_vec_name'] = 'aposp.1D'

print vars['reg_subjects']

rrdata = RRData(vars)
rrdata.instantiate_all()

RegReg = RegRegPipe(rrdata)
RegReg.run()

#minigrid = MG(vars, RegReg, prefix='wrsub')
#minigrid.run()





