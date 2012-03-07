#!/usr/bin/env python

import sys, os
import glob
import api
from pprint import pprint
import simplejson
import time
from MiniGridsearch import MiniGridsearch as MG


def openjs(name):
    file = open(name,'r')
    return simplejson.load(file)
    
def parsename(name):
    s = name.split('_')
    b1 = float(s[1])
    b2 = float(s[2])
    b3 = float(s[3].strip('.json'))
    return [b1,b2,b3]
    
def getacc(d):
    return float(d['mean_accuracy'])

def values(name):
    d = openjs(name)
    nbvals = parsename(name)
    bvals = [name]
    bvals.append(getacc(d))
    nbvals.append(getacc(d))
    return [bvals,nbvals]

def sortbyacc(tests,ind):
    return sorted(tests, key=lambda list: list[ind])


def getmaxname(sort):
    maxval = 0
    maxname = ''
    for test in sort:
        if test[1] > maxval:
            maxval = test[1]
            maxname = test[0]
    return maxname
    

def mini_gridsearch(seed,vars,supermax):
    b1mults = [0.1, 0.33, 0.66, 1.33, 1.66]
    b2mults = [0.01, 0.1, 0.25, 0.5]
    b3mults = [0.01, 0.1, 0.25, 0.5]
    
    for b1m in b1mults:
        for b2m in b2mults:
            for b3m in b3mults:
                
                time.sleep(0.5)
                
                done = 0
                rlist = glob.glob('../reg_output/records/*.json')
                for file in rlist:
                    [b1,b2,b3] = parsename(os.path.split(file)[1])
                    if [seed*b1m, seed*b1m*b2m, seed*b1m*b3m] == [b1,b2,b3]:
                        done = 1
                if not done:
                    vars['bound1'] = seed*b1m
                    vars['bound2'] = seed*b1m*b2m
                    vars['bound3'] = seed*b1m*b3m
                    
                    x = '_'+str(vars['bound1'])+'_'+str(vars['bound2'])+'_'+str(vars['bound3'])
                    
                    #outfs = ['rr'+x+'_half','rr'+x+'_pos','rr'+x+'_neg']
                    #respvs = ['achoosehalf.1D','achoosepos.1D','achooseneg.1D']
                    #onsetfs = ['ahalfp.1D','aposp.1D','anegp.1D']
                    
                    outfs = ['rr'+x+'_half']
                    respvs = ['achoosehalf.1D']
                    onsetfs = ['ahalfp.1D']
                    
                    for out,res,ons in zip(outfs,respvs,onsetfs):
                    
                        vars['output_filename'] = out
                        vars['reg_resp_vec_name'] = res
                        vars['reg_onset_vec_name'] = ons
                        
                        print vars['output_filename']
                        print vars['reg_resp_vec_name']
                        print vars['reg_onset_vec_name']
                        print vars['bound1']
                        print vars['bound2']
                        print vars['bound3']
                    
                        RegReg = api.RegRegPipe()
                        RegReg.initialize_variables(vars)
                        RegReg.run()
    
    os.chdir('./reg_output/records/')        
    jsons = glob.glob('*.json')
    bvals = []
    for name in jsons:
        vals,n = values(name)
        bvals.append(vals)
    bvals = sortbyacc(bvals,1)
    mname,maxacc = getmaxes(bvals)
    [maxb1,maxb2,maxb3] = parsename(name)
    os.chdir('../../')
    if (supermax >= maxacc) or (maxb1 == seed):
        return maxb1
    else:
        mini_gridsearch(maxb1,vars,maxacc)
    
                    
if __name__ == '__main__':
    
    # initialize variable dictionary:
    vars = {}
    
    # determine if using cni or lucas:
    data_type = 'cni'
    
    # list the subjects to be processed:
    exclude_dirs = ['exclude','scripts','spanprocessor','timecourses','ttest',\
                    'dd083111','dk091611','ju083111','mm110111','reg_output']
    subjects = []
    vars['subjects'] = subjects
    
    # cni variables:
    raw_anat = '0006_01_T1w_9mm_BRAVO.nii.gz'
    raw_funcs = ['0004_01_BOLD_EPI_29mm_2sec.nii.gz','0005_01_BOLD_EPI_29mm_2sec.nii.gz']
    raw_funcs_alternate = ['04_BOLD_EPI_29mm_2sec_1_0.nii.gz','05_BOLD_EPI_29mm_2sec_1_0.nii.gz']
    func_names = ['pasreg','actreg']
    
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
    if subjects:
        vars['subject_dirs'] = api.parse_dirs(prefixes=subjects)
    elif exclude_dirs:
        vars['subject_dirs'] = api.parse_dirs(exclude=exclude_dirs)
    vars['raw_funcs'] = raw_funcs
    vars['raw_funcs_alt'] = raw_funcs_alternate
    vars['raw_anat'] = raw_anat
    vars['func_names'] = func_names
    vars['dynamic_iti'] = True
    
    
    # reg reg vars:
    vars['log_filename'] = 'ratreg_log'
    vars['output_filename'] = 'ratreg3_half'
    vars['reg_nifti_name'] = 'actepin_reg.nii'
    vars['reg_mask_name'] = 'talairach_mask.nii'
    vars['reg_response_tr'] = 3
    vars['reg_subjects'] = vars['subject_dirs']
    vars['reg_total_trials'] = 72
    vars['reg_prediction_tr_len'] = 1
    vars['lag'] = 2
    vars['reg_trial_trs'] = 4
    # start tr of interest at 1, not 0:
    vars['trs_of_interest'] = [1] 
    vars['reg_mask_dir'] = 'reg_output'
    vars['reg_save_dir'] = 'reg_output'
    vars['random_seed'] = 1356394
    vars['warm_start'] = True
    vars['crossvalidation_folds'] = 1
    vars['downsample_type'] = 'group'
    
    vars['loss'] = 'quadratic'
    vars['penalties'] = ['sparsity_bound', 'graphnet_bound_smooth', 'ridge_bound_smooth','graphnet']

    #vars['bound1'] = 2.0
    #vars['bound2'] = 1.
    #vars['bound3'] = 0.01
    
    vars['inv_step'] = 1500000.
    vars['set_tol'] = 1e-04
    vars['max_its'] = 1000
    
    
    vars['lookback'] = False
    vars['lookback_trs'] = 0
    vars['use_mask'] = True
        
    
    vars['reg_resp_vec_name'] = 'achoosehalf.1D'
    vars['reg_onset_vec_name'] = 'ahalfp.1D'
    RegReg = api.RegRegPipe()
    minigrid = MG(vars,RegReg)
    minigrid.run()
        
    #mini_gridsearch(2.0,vars,0.)
    '''
    vars['bound1'] = 0.01
    vars['bound2'] = 0.01
    vars['bound3'] = 0.01
    
    x = '_'+str(vars['bound1'])+'_'+str(vars['bound2'])+'_'+str(vars['bound3'])
    
    #outfs = ['rr'+x+'_half','rr'+x+'_pos','rr'+x+'_neg']
    #respvs = ['achoosehalf.1D','achoosepos.1D','achooseneg.1D']
    #onsetfs = ['ahalfp.1D','aposp.1D','anegp.1D']
    
    outfs = ['rr'+x+'_half']
    respvs = ['achoosehalf.1D']
    onsetfs = ['ahalfp.1D']
    
    for out,res,ons in zip(outfs,respvs,onsetfs):
    
        vars['output_filename'] = out
        vars['reg_resp_vec_name'] = res
        vars['reg_onset_vec_name'] = ons
        
        print vars['output_filename']
        print vars['reg_resp_vec_name']
        print vars['reg_onset_vec_name']
        print vars['bound1']
        print vars['bound2']
        print vars['bound3']
    
        RegReg = api.RegRegPipe()
        RegReg.initialize_variables(vars)
        RegReg.run()
    '''
        
    

