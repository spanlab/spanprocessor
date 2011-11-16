#!/usr/bin/env python

import os, sys
import re
import api
from pprint import pprint

class PipeWrapper(object):
    def __init__(self):
        self.vars = {}
        api.set_standard_defaults(self.vars)
        self.preprocess = True
        self.threads = 4
        self.subjects = []
        self.exclude_dirs = []
        self.data_type = []
        self.func_names = []
        
        #cni:
        self.anat_scan_num = []
        self.func_scan_nums = []
        
        #requirements:
        self.__preprocess_reqs = ['data_type','anat_scan_num','func_scan_nums',
                                  'func_names']
        self.__generic_exclude = ['exclude','scripts','spanprocessor',
                                  'timecourses','ttest','skripts']
        
    def do_all_subjects(self):
        self.subjects = []
    
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
            if check:
                self.autofill_scan_info()
            if self.__check_scripts_dir():
                os.chdir('../')
            MasterProc = api.Master(self.threads,self.vars)
            MasterProc.preprocess()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            