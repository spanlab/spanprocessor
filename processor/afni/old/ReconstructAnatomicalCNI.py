#!/usr/bin/env python

from AfniProcess import AfniProcess


class ReconstructAnatomicalCNI(AfniProcess):
    def __init__(self,anat_name=None,raw_anat=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['anat_name','raw_anat']
        self.anat_name = anat_name
        self.raw_anat = raw_anat
        
        
    def outputs(self):
        self.outputs = {'dset_out':self.anat_name}
        return self.outputs
    
    def commands(self):
        general_cleaner(self.anat_name,1)
        shell_command(['3dcopy',self.raw_anat,self.anat_name])