#!/usr/bin/env python

from AfniProcess import AfniProcess

class WarpFunctionals(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_mbnf',anat_name=None,talairach_dxyz=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','anat_name','talairach_dxyz']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.anat_name = anat_name
        self.talairach_dxyz = talairach_dxyz
        
        
    def output(self):
        self.outputs = {'dset_out':[(x+self.suffix_in) for x in self.dset_labels],
            'suffix_out':self.suffix_in}
        return self.outputs
    
        
    def commands(self):
        for i,epi in enumerate(self.dset_labels):
            shell_command(['adwarp','-apar',self.anat_name+'+tlrc','-dpar',epi+self.suffix_in+'+orig',
                           '-dxyz',str(self.talairach_dxyz)])