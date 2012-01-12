#!/usr/bin/env python

from pprint import pprint
from mono_utility import (shell_command, parse_dirs)
import sys, os
import glob


class Variables():
    def __init__(self):
        self.talairach_path_osx = '/Users/span/abin/TT_N27+tlrc'
        self.talairach_path_linux = '/usr/local/afni/bin/TT_N27+tlrc'
        if sys.platform == 'linux2':
            self.talairach_path = self.talairach_path_linux
        elif sys.platform == 'darwin':
            self.talairach_path = self.talairach_path_osx
    
        
    def set(self,**kwargs):
        for arg,val in kwargs.items():
            setattr(self,argument,value)
        
        
    def check(self,*args):
        output = []
        for var_name in args:
            if not getattr(self,var_name,None):
                print(var_name+' is not set, or is None.\n')
                output.append(None)
            else:
                output.append(getattr(self,var_name))
        return output
    
    
    def set_knutson_defaults(self):
        self.tr_time = 2.0
        self.leadin = 6
        self.leadout = 4
        self.anat_name = 'anat'
        self.scripts_dir = 'scripts'
        self.preprocess_outdir = './'
        self.talairach_dxyz = 2.9
        self.dynamic_iti = True
        self.motionfile_prefix = '3dmotion'
        self.tr_bytes = 393216
        self.outdir = './'
        
        
    def set_regreg_defaults(self):
        # should only use either of the two bounds, for the other use the
        # lagrange.
        self.lambda1 = 11.
        # higher bound 1 -> more coefficients 
        self.bound1 = 0.0012
        # higher lambda 2 -> more smoothness
        self.lambda2 = 1.5
        self.lambda3 = 0.
        self.bound3 = 1.0e0
        self.inv_step = 1500000.
        self.set_tol = 1e-10
        self.max_its = 1000
        self.lookback = False
        self.lookback_trs = 0
        self.use_mask = True
    
    def cni_find_raw_functionals(vars_dict):
        proceed = True
        currentdir = os.getcwd()
        if not getattr(self,'subject_dirs',None):
            if not getattr(self,'subjects',None):
                proceed = False
                print('Cannot proceed without subjects variable defined.\n')
            else:
                setattr(self,'subject_dirs',parse_dirs(prefixes=self.subjects))
        if not getattr(self,'func_scan_nums',None):
            proceed = False
            print('Cannot proceed without functional scan numbers defined.\n')
        if proceed:
            os.chdir(self.subject_dirs[0])
            raw_names = []
            nii_num_pairs = []
            nii_files_zipped = glob.glob('*.nii.gz')
            for nii in nii_files_zipped:
                scan_num = int((nii.split('_'))[0])
                nii_num_pairs.append([nii,scan_num])
            for num in self.func_scan_nums:
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
                self.raw_funcs = raw_names
                pprint(raw_names)
                pprint('Raw functionals established.\n')
                return True
            else:
                pprint('No raw functionals established.\n')
                return False


    def cni_find_trs_slices(self):
        # should convert this to use 're' module later...
        proceed = True
        if not getattr(self,'subjects',None):
            print 'ERROR: Cannot calculate TRs and slices without at least 1 subject specified.\n'
            proceed = False
        elif not getattr(self,'raw_funcs',None):
            print 'No raw_funcs specified, attempting to acquire...\n'
            if not getattr(self,'func_scan_nums',None):
                print 'ERROR: Cannot calculate TRs or slices without func_scan_nums specified.\n'
                proceed = False
            else:
                proceed = self.cni_find_raw_functionals()
        if proceed:
            if not getattr(self,'subject_dirs',None):
                self.subject_dirs = parse_dirs(prefixes=self.subjects)
            pprint(self.subject_dirs)
            os.chdir(self.subject_dirs[0])
            [trs,slices] = self._rip_funcs_info(self.raw_funcs)
            trxslices = self._calc_trxslices(trs,slices)
            self.trs = trs
            self.nslices = slices
            self.trxslices = trxslices
            os.chdir('../')
            
            

    def _calc_trxslices(self,trs,slices):
        trxslices = []
        for x,y in zip(trs,slices):
            if type(x) == type([]):
                if not type(y) == type([]):
                    print 'ERROR: mismatch in trs and slices.\n\n'
                else:
                    sub_trxslices = self._calc_trxslices(x,y)
                    trxslices.append(sub_trxslices)
            else:
                if type(y) == type([]):
                    print 'ERROR: mismatch in trs and slices.\n\n'
                else:
                    trxslice = x*y
                    trxslices.append(trxslice)
        return trxslices
        
    def _rip_funcs_info(self,funcs):
        trs = []
        slices = []
        for func in funcs:
            if type(func) == type([]):
                [sub_trs,sub_slices] = self._rip_funcs_info(func)
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
    

    def define_leadouts(self):
        if None in [getattr(self,x,None) for x in ['trs','leadout']]:
            print 'ERROR: trs, and leadout must be defined in dict to calculate leadouts.\n'
        else:
            self.leadouts = []
            for tr in self.trs:
                if type(tr) == type([]):
                    sub_leadout = [x-int(self.leadout)-1 for x in tr]
                    leadouts.append(sub_leadout)
                else:
                    single_leadout = tr-int(self.leadout)-1
                    leadouts.append(single_leadout)
    
        
    def set_motion_labels(self,suffixes=False):
        if not getattr(self,'motionfile_prefix',None):
            prefix = '3dmotion'
        else:
            prefix = self.motionfile_prefix
        number_of_funcs = 0
        auto_suffixes = []
        if not getattr(self,'func_names',None):
            print 'func_names not defined in dict, checking raw_funcs...\n'
            if not getattr(self,'raw_funcs',None):
                print 'WARNING: Neither func_names nor raw_funcs defined in dict.\n'
            else:
                number_of_funcs = len(self.raw_funcs)
                auto_suffixes = [('_%s' % str(i+1)) for i in range(number_of_funcs)]
        else:
            number_of_funcs = len(self.func_names)
            auto_suffixes = [('_%s' % x) for x in self.func_names]
        if not suffixes and not number_of_funcs:
            print 'ERROR: Unable to create motion prefixes.\nUser must define prefixes or set raw_funcs/func_names.\n'
        elif not suffixes:
            motion_labels = [(prefix+suff) for suff in auto_suffixes]
        else:
            motion_labels = [(prefix+suff) for suff in suffixes]
        self.motion_labels = motion_labels
        
    

    
    
    
    
