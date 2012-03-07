#!/usr/bin/env python

from AfniProcess import AfniProcess



class CorrectMotion(AfniProcess):
    def __init__(self,dset_labels=None,motion_labels=None,suffix_in='',suffix_out='_m'):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','motion_labels','suffix_in','suffix_out']
        self.dset_labels = dset_labels
        self.motion_labels = motion_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        
        
    def output(self):
        self.outputs = {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],
            'suffix_out':self.suffix_out,'motion_files':[label for label in self.motion_labels]}
        
    def commands(self):
        if len(self.motion_labels) != len(self.dset_labels):
            print('\nWARNING: Motion labels not equal to number of functionals.\n')
        else:
            for i,(label,epi) in enumerate(zip(self.motion_labels,self.dset_labels)):
                # clean out motion files:
                general_cleaner(label,0)
                general_cleaner(epi+self.suffix_out,1)
                # run 3dvolreg for each functional:
                shell_command(['3dvolreg','-Fourier','-twopass','-prefix',epi+self.suffix_out,'-base',
                               '3','-dfile',label+'.1D',epi+self.suffix_in+'+orig'])
