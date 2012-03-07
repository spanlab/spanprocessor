#!/usr/bin/env python

from AfniProcess import AfniProcess



class MaskWarpedFunctionals(AfniProcess):
    def __init__(self,dset_labels=None,scripts_dir='scripts',talairach_path=None,
                 suffix_in='_mbnf',suffix_out='_masked',talairach_dxyz=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','scripts_dir','talairach_path',
                                'suffix_in','suffix_out','talairach_dxyz']
        self.dset_labels = dset_labels
        self.scripts_dir = scripts_dir
        self.talairach_path = talairach_path
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.talairach_dxyz = talairach_dxyz
        
        
    def output(self):
        self.outputs = {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],
            'suffix_out':self.suffix_out}
        return self.outputs
    
    def commands(self):
        currentdir = os.getcwd()
        for epi in self.dset_labels:
            os.chdir('../'+self.scripts_dir)
            if not os.path.exists('./talairach_mask+tlrc.HEAD'):
                shutil.copy(self.talairach_path+'.HEAD','./'+self.talairach_path.split('/')[-1]+'.HEAD')
                shutil.copy(self.talairach_path+'.BRIK.gz','./'+self.talairach_path.split('/')[-1]+'.BRIK.gz')
                shell_command(['3dresample','-dxyz',str(self.talairach_dxyz),str(self.talairach_dxyz),
                               str(talairach_dxyz),'-prefix','talairach_resamp','-inset',
                               talairach_path.split('/')[-1]])
                shell_command(['3dAutomask','-prefix','talairach_mask','-clfrac','0.1','talairach_resamp+tlrc'])
                shell_command(['3dAFNItoNIFTI','-prefix','talairach_mask','talairach_mask+tlrc'])
            os.chdir(currentdir)
            general_cleaner(epi+self.suffix_out,1)
            shell_command(['3dcalc','-a',epi+self.suffix_in+'+tlrc','-b',
                           '../'+self.scripts_dir+'/talairach_mask+tlrc',
                           '-expr', 'a*step(b)','-prefix',epi+self.suffix_out])
            shell_command(['3dAFNItoNIFTI','-prefix',epi+self.suffix_out,epi+self.suffix_out+'+tlrc'])
            
            
            