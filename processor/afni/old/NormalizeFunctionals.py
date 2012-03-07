#!/usr/bin/env python

from AfniProcess import AfniProcess



class NormalizeFunctionals(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_mb',suffix_out='_mbn',calc_precision='float'):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','suffix_out','calc_precision']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.calc_precision = calc_precision
        
        
    def outputs(self):
        self.outputs = {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],
            'suffix_out':self.suffix_out}
        return self.outputs
        
    def commands(self):
        for i,epi in enumerate(self.dset_labels):
            general_cleaner(epi+self.suffix_out,1)
            general_cleaner(epi+'_average',1)
            shell_command(['3dTstat','-prefix',epi+'_average',epi+self.suffix_in+'+orig'])
            shell_command(['3drefit','-abuc',epi+'_average+orig'])
            shell_command(['3dcalc','-datum',self.calc_precision,'-a',epi+self.suffix_in+'+orig',
                           '-b',epi+'_average+orig','-expr','((a-b)/b)*100',
                           '-prefix',epi+self.suffix_out])