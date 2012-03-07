#!/usr/bin/env python

from AfniProcess import AfniProcess


class BlurFunctionals(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_m',suffix_out='_mb',kernel=4):
        AfniProcess.__init__(self)
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.kernel = kernel

    
    def commands(self):
        for func in self.dset_labels:
            general_cleaner(func+self.suffix_out,1)
            shell_command(['3dmerge','-prefix',func+self.suffix_out,'-1blur_fwhm',str(self.kernel),
                           '-doall',func+self.suffix_in+'+orig'])
