#!/usr/bin/env python

from AfniProcess import AfniProcess



class ConvertToNifti(AfniProcess):
    def __init__(self,dset_labels=None,afni_format='+tlrc'):
        AfniProcess.__init__(self)
        self.dset_labels = dset_labels
        self.afni_format = afni_format

        
    def commands(self):
        for dset in self.dset_labels:
            shell_command(['3dAFNItoNIFTI','-prefix',dset,dset+self.afni_format])


        
        