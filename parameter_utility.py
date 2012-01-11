#!/usr/bin/env python

from pprint import pprint
from mono_utility import (shell_command, parse_dirs)
import sys, os
import glob

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

def kiefer_defaults(vars_dict):
    vars_dict['tr_time'] = 5.0

def set_regreg_defaults(vars_dict):
    # should only use either of the two bounds, for the other use the
    # lagrange.
    vars_dict['lambda1'] = 11.
    # higher bound 1 -> more coefficients 
    vars_dict['bound1'] = 0.0012
    # higher lambda 2 -> more smoothness
    vars_dict['lambda2'] = 1.5
    vars_dict['lambda3'] = 0.
    vars_dict['bound3'] = 1.0e0
    vars_dict['inv_step'] = 1500000.
    vars_dict['set_tol'] = 1e-10
    vars_dict['max_its'] = 1000
    vars_dict['lookback'] = False
    vars_dict['lookback_trs'] = 0
    vars_dict['use_mask'] = True
    
def set_variables(vars_dict,**kwargs):
    for key,value in kwargs.iteritems():
        vars_dict[key] = value

def cni_find_func_raws_old(vars_dict):
    currentdir = os.getcwd()
    if not 'subject_dirs' in vars_dict:
        vars_dict['subject_dirs'] = parse_dirs(prefixes=vars_dict['subjects'])
    os.chdir(vars_dict['subject_dirs'][0])
    raw_names = []
    nii_files_zipped = glob.glob('*.nii.gz')
    for nii in nii_files_zipped:
        scan_num = int((nii.split('_'))[0])
        if scan_num in vars_dict['func_scan_nums']:
            raw_names.append(nii)
    os.chdir(currentdir)
    if not raw_names == []:
        vars_dict['raw_funcs'] = raw_names
        return True
    else:
        return False
    
def cni_find_func_raws(vars_dict):
    currentdir = os.getcwd()
    if not 'subject_dirs' in vars_dict:
        vars_dict['subject_dirs'] = parse_dirs(prefixes=vars_dict['subjects'])
    os.chdir(vars_dict['subject_dirs'][0])
    raw_names = []
    nii_num_pairs = []
    nii_files_zipped = glob.glob('*.nii.gz')
    for nii in nii_files_zipped:
        scan_num = int((nii.split('_'))[0])
        nii_num_pairs.append([nii,scan_num])
    for num in vars_dict['func_scan_nums']:
        if type(num) == type([]):
            raw_block = []
            for sub_num in num:
                for pair in nii_num_pairs:
                    if pair[1] == sub_num:
                        raw_block.append(pair[0])
            raw_names.append(raw_block)
        else:
            for pair in nii_num_pairs:
                if pair[1] == num:
                    raw_names.append(pair[0])
    os.chdir(currentdir)
    if not raw_names == []:
        vars_dict['raw_funcs'] = raw_names
        pprint(raw_names)
        return True
    else:
        return False
    
''' DEPRECATED FUNCTION VERSIONS:
    
def cni_find_trs_slices(vars_dict):
    # should convert this to use 're' module later...
    flag = True
    if not 'subjects' in vars_dict:
        print 'ERROR: Cannot calculate TRs and slices without at least 1 subject specified.\n'
        flag = False
    elif not 'raw_funcs' in vars_dict:
        print 'No raw_funcs specified, attempting to acquire...\n'
        if not 'func_scan_nums' in vars_dict:
            print 'ERROR: Cannot calculate TRs or slices without func_scan_nums specified.\n'
            flag = False
        else:
            flag = cni_find_func_raws(vars_dict)
    if flag:
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

''' 

def cni_find_trs_slices(vars_dict):
    # should convert this to use 're' module later...
    flag = True
    if not 'subjects' in vars_dict:
        print 'ERROR: Cannot calculate TRs and slices without at least 1 subject specified.\n'
        flag = False
    elif not 'raw_funcs' in vars_dict:
        print 'No raw_funcs specified, attempting to acquire...\n'
        if not 'func_scan_nums' in vars_dict:
            print 'ERROR: Cannot calculate TRs or slices without func_scan_nums specified.\n'
            flag = False
        else:
            flag = cni_find_func_raws(vars_dict)
    if flag:
        print vars_dict['subjects']
        if not 'subject_dirs' in vars_dict:
            vars_dict['subject_dirs'] = parse_dirs(prefixes=vars_dict['subjects'])
        print vars_dict['subject_dirs']
        os.chdir(vars_dict['subject_dirs'][0])
        funcs = vars_dict['raw_funcs']
        [trs,slices] = rip_funcs_info(funcs)
        trxslices = calc_trxslices(trs,slices)
        vars_dict['trs'] = trs
        vars_dict['nslices'] = slices
        vars_dict['trxslices'] = trxslices
        os.chdir('../')

def calc_trxslices(trs,slices):
    trxslices = []
    for x,y in zip(trs,slices):
        if type(x) == type([]):
            if not type(y) == type([]):
                print 'ERROR: mismatch in trs and slices.\n\n'
            else:
                sub_trxslices = calc_trxslices(x,y)
                trxslices.append(sub_trxslices)
        else:
            if type(y) == type([]):
                print 'ERROR: mismatch in trs and slices.\n\n'
            else:
                trxslice = x*y
                trxslices.append(trxslice)
    return trxslices
        
def rip_funcs_info(funcs):
    trs = []
    slices = []
    for func in funcs:
        if type(func) == type([]):
            [sub_trs,sub_slices] = rip_funcs_info(func)
            trs.append(sub_trs)
            slices.append(sub_slices)
        else:
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
    return [trs,slices]
    

def define_leadouts(vars_dict):
    if not [(x in vars_dict) for x in ['trs','leadout']] == [True,True]:
        print 'ERROR: trs, and leadout must be defined in dict to calculate leadouts.\n'
    else:
        trs = vars_dict['trs']
        leadout = vars_dict['leadout']
        leadouts = []
        for tr in trs:
            if type(tr) == type([]):
                sub_leadout = [x-int(leadout)-1 for x in tr]
                leadouts.append(sub_leadout)
            else:
                single_leadout = tr-int(leadout)-1
                leadouts.append(single_leadout)
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
        
    

    
    
    
    
