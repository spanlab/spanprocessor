#!/usr/bin/env python

from AfniProcess import AfniProcess


class ReconstructFunctionalsCNI(AfniProcess):
    def __init__(self,dset_labels=None,raw_funcs=None,leadin=None,leadouts=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','raw_funcs','leadin','leadouts']
        self.dset_labels = dset_labels
        self.raw_funcs = raw_funcs
        self.leadin = leadin
        self.leadouts = leadouts
        self.suffix_out = ''
        
        
    def output(self):
        self.outputs = {'dset_out':[x for x in self.dset_labels],'suffix_out':self.suffix_out}
        return self.outputs
        
    def commands(self):
        general_cleaner(self.dset_labels,1)
        if len(self.raw_funcs) != len(self.dset_labels):
            print('\nWARNING: Functional labels not equal to number of functionals.\n')
        else:
            for i,(name,raw) in enumerate(zip(self.dset_labels,self.raw_funcs)):
                if type(raw) == type([]):
                    for j,nraw in enumerate(raw):
                        shell_command(['3dTcat','-prefix',name+str(j),nraw+'['+str(self.leadin)+'..'+str(self.leadouts[i][j])+']'])
                    cat = [(name+str(j)+'+orig') for j in range(len(raw))]
                    cmd = ['3dTcat','-prefix',name]
                    cmd = cmd.extend(cat)
                    shell_command(cmd)
                elif os.path.exists('./'+raw):
                    shell_command(['3dTcat','-prefix',name,raw+'['+str(self.leadin)+'..'+str(self.leadouts[i])+']'])

