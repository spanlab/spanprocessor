#!/usr/bin/env python

from AfniProcess import AfniProcess

class WarpAnatomical(AfniProcess):
    def __init__(self,anat_name=None,talairach_path=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['anat_name','talairach_path']
        self.anat_name = anat_name
        self.talairach_path = talairach_path
        
        
    def output(self):
        self.outputs = {'dset_out':self.anat_name}
        return self.outputs
    
    def commands(self):
        shell_command(['@auto_tlrc','-warp_orig_vol','-suffix','NONE','-base',
                       self.talairach_path,'-input',self.anat_name+'+orig'])