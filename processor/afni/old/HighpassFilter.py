#!/usr/bin/env python

from AfniProcess import AfniProcess



class HighpassFilter(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_mbn',suffix_out='_mbnf',highpass_val=.011):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','suffix_out','highpass_val']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.highpass_val = highpass_val
        
        
    def output(self):
        self.outputs = {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],
            'suffix_out':self.suffix_out}
        return self.outputs
        
    def commands(self):
        for i,epi in enumerate(self.dset_labels):
            general_cleaner(epi+self.suffix_out,1)
            shell_command(['3dFourier','-prefix',epi+self.suffix_out,'-highpass',
                           str(self.highpass_val),epi+self.suffix_in+'+orig'])