#!/usr/bin/env python

import os, sys
import re
import api
from pprint import pprint

class PipeWrapper(object):
    def __init__(self):
        self.vars = {}
        api.set_standard_defaults(self.vars)
        self.threads = 4
        self.subjects = []
        self.exclude_dirs = []
        self.data_type = []
        self.func_names = []
        
        #cni:
        self.anat_scan_num = []
        self.func_scan_nums = []
        
        #preprocess specific:
        self.preprocess = True
        self.do_anat_reconstruction = True
        self.do_func_reconstruction = True
        self.do_warp_anatomical = True
        self.do_correct_motion = True
        self.do_normalize = True
        self.do_highpass_filter = True
        self.do_warp_functionals = True
        self.do_mask_functionals = True
        self.do_convert_to_nifti = True
        
        #requirements:
        self.__preprocess_reqs = ['data_type','anat_scan_num','func_scan_nums',
                                  'func_names']
        self.__generic_exclude = ['exclude','scripts','spanprocessor',
                                  'timecourses','ttest','skripts']
        
    def __pack_preprocess_flags(self):
        prep_package = {'do_anat_reconstruction':self.do_anat_reconstruction,
                        'do_func_reconstruction':self.do_func_reconstruction,
                        'do_warp_anatomical':self.do_warp_anatomical,
                        'do_correct_motion':self.do_correct_motion,
                        'do_normalize':self.do_normalize,
                        'do_highpass_filter':self.do_highpass_filter,
                        'do_warp_functionals':self.do_warp_functionals,
                        'do_mask_functionals':self.do_mask_functionals,
                        'do_convert_to_nifti':self.do_convert_to_nifti}
        return prep_package
    
    def __check_preprocess_reqs(self):
        flag = True
        for name,var in zip(self.__preprocess_reqs,[self.data_type,self.anat_scan_num,
                                                    self.func_scan_nums,self.func_names]):
            if var == []:
                print 'ERROR: '+name+' is not set. Cannot run.\n\n'
                flag = False
            else:
                self.vars[name] = var
        if not flag:
            return False
        else:
            return True
    
    def __check_scripts_dir(self):
        dir = os.getcwd()
        if [(dir.endswith(x)) for x in ['skripts','scripts','spanprocessor']] == [False,False,False]:
            return False
        else:
            return True
    
    def autofill_scan_info(self):
        if self.__check_scripts_dir():
            os.chdir('../')
        if self.subjects:
            self.vars['subjects'] = self.subjects
            self.vars['subject_dirs'] = api.parse_dirs(prefixes=self.subjects)
        elif self.exclude_dirs:
            self.vars['subject_dirs'] = api.parse_dirs(exclude=self.exclude_dirs.extend(self.__generic_exclude))
        else:
            self.vars['subject_dirs'] = api.parse_dirs(exclude=self.__generic_exclude)
        pprint(self.vars['subject_dirs'])
        pprint(self.subjects)
        api.cni_find_trs_slices(self.vars)
        api.define_leadouts(self.vars)
        api.set_motion_labels(self.vars)
    
    def run(self):
        if self.preprocess:
            check = self.__check_preprocess_reqs()
            flags = self.__pack_preprocess_flags()
            if check:
                self.autofill_scan_info()
            if self.__check_scripts_dir():
                os.chdir('../')
            MasterProc = api.Master(self.threads,self.vars)
            MasterProc.preprocess(flags)
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            