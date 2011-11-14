#!/usr/bin/env python

from mono_utility import (shell_command, parse_dirs)
import sys, os

def set_standard_defaults(vars_dict):
    vars_dict['tr_time'] = 2.0
    vars_dict['leadin'] = 6
    vars_dict['leadout'] = 4
    vars_dict['anat_name'] = 'anat'
    vars_dict['talairach_path_osx'] = '/Users/span/abin/TT_N27+tlrc'
    vars_dict['talairach_path_linux'] = '/usr/local/afni/bin/TT_N27+tlrc'
    if sys.platform == 'linux2':
        vars_dict['talairach_path'] = vars_dict['talairach_path_linux']
    elif sys.platform == 'darwin':
        vars_dict['talairach_path'] = vars_dict['talairach_path_osx']
    vars_dict['scripts_dir'] = 'scripts'
    vars_dict['preprocess_outdir'] = './'
    vars_dict['talairach_dxyz'] = 2.9
    vars_dict['dynamic_iti'] = True
    vars_dict['motionfile_prefix'] = '3dmotion'
    vars_dict['tr_bytes'] = 393216
    vars_dict['outdir'] = './'

def set_regreg_defaults(vars_dict):
    vars_dict['lambda1'] = 11.
    vars_dict['bound1'] = 2.
    vars_dict['lambda2'] = 1.
    #vars_dict['lambda3'] = 10000000.
    vars_dict['lambda3'] = 100000.
    vars_dict['bound3'] = 1.0e0
    vars_dict['inv_step'] = 15000.
    vars_dict['set_tol'] = 1e-6
    vars_dict['max_its'] = 400
    vars_dict['lookback'] = False
    vars_dict['lookback_trs'] = 0
    
def set_variables(vars_dict,**kwargs):
    for key,value in kwargs.iteritems():
        vars_dict[key] = value

    
def cni_find_trs_slices(vars_dict):
    # should convert this to use 're' module later...
    if not 'raw_funcs' in vars_dict:
        print 'ERROR: Cannot calculate TRs or slices without raw_funcs specified.\n'
    elif not 'subjects' in vars_dict:
        print 'ERROR: Cannot calculate TRs and slices without at least 1 subject specified.\n'
    else:
        print vars_dict['subjects']
        if not 'subject_dirs' in vars_dict:
            vars_dict['subject_dirs'] = parse_dirs(prefixes=vars_dict['subjects'])
        print vars_dict['subject_dirs']
        os.chdir(vars_dict['subject_dirs'][0])
        funcs = vars_dict['raw_funcs']
        trs = []
        slices = []
        print os.getcwd()
        for func in funcs:
            info = shell_command(['3dinfo',func],ioflag=True)
            linedinfo = info.split('\n')
            rip_line = []
            rip_parse = []
            for line in linedinfo:
                if line.find('Number of time steps') != -1:
                    rip_line = line.split(' ')
            for item in rip_line:
                if len(item) != 0:
                    rip_parse.append(item)
            trs.append(int(rip_parse[5]))
            slices.append(int(rip_parse[17]))
        trxslices = [x*y for x in trs for y in slices]
        vars_dict['trs'] = trs
        vars_dict['nslices'] = slices
        vars_dict['trxslices'] = trxslices
        os.chdir('../')

def define_leadouts(vars_dict):
    if not [(x in vars_dict) for x in ['trs','leadout']] == [True,True]:
        print 'ERROR: trs, and leadout must be defined in dict to calculate leadouts.\n'
    else:
        trs = vars_dict['trs']
        leadout = vars_dict['leadout']
        leadouts = [x-int(leadout)-1 for x in trs]
        vars_dict['leadouts'] = leadouts
        
def set_motion_labels(vars_dict,suffixes=False):
    if not 'motionfile_prefix' in vars_dict:
        prefix = '3dmotion'
    else:
        prefix = vars_dict['motionfile_prefix']
    number_of_funcs = 0
    auto_suffixes = []
    if not 'func_names' in vars_dict:
        print 'func_names not defined in dict, checking raw_funcs...\n'
        if not 'raw_funcs' in vars_dict:
            print 'WARNING: Neither func_names nor raw_funcs defined in dict.\n'
        else:
            number_of_funcs = len(vars_dict['raw_funcs'])
            auto_suffixes = [('_%s' % str(i+1)) for i in range(number_of_funcs)]
    else:
        number_of_funcs = len(vars_dict['func_names'])
        auto_suffixes = [('_%s' % x) for x in vars_dict['func_names']]
    if not suffixes and not number_of_funcs:
        print 'ERROR: Unable to create motion prefixes.\nUser must define prefixes or set raw_funcs/func_names.\n'
    elif not suffixes:
        motion_labels = [(prefix+suff) for suff in auto_suffixes]
    else:
        motion_labels = [(prefix+suff) for suff in suffixes]
    vars_dict['motion_labels'] = motion_labels
        
    

    
    
    
    
