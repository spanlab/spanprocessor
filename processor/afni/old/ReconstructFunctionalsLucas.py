#!/usr/bin/env python

from AfniProcess import AfniProcess


class ReconstructFunctionalsLucas(AfniProcess):
    def __init__(self,dset_labels=None,pfiles_by_func=None,tr_bytes=393216,
                 nslices=None,isvalues=None,tr_time=None,leadin=None,leadout=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','pfiles_by_func','tr_bytes','nslices',
                                'isvalues','tr_time','leadin','leadout']
        self.dset_labels = dset_labels
        self.pfiles_by_func = pfiles_by_func
        self.tr_bytes = tr_bytes
        self.nslices = nslices
        self.isvalues = isvalues
        self.tr_time = tr_time
        self.leadin = leadin
        self.leadout = leadout
        self.tcat_suffix = '_crop'
        self.tshift_suffix = '_cropts'
        
    def output(self):
        self.outputs = {'dset_out':[(x+self.tshift_suffix) for x in self.dset_labels],
            'suffix_out':self.tshift_suffix}
        return self.outputs
        
    def _parse_psizes(self,pfiles,tr_bytes):
        sizes = []
        for file in pfiles:
            size = shell_command(['du','-b',file],ioflag=1)
            size = size.strip(' \n\t')
            sizes.append([file,int(size[0])])
        # calculate TR from filesize + hardcoded bytes per TR:
        for i in range(len(sizes)):
            sizes[i][1] = int(math.floor(sizes[i][1]/tr_bytes))
        return sizes    
    
    def _assign_pfiles(self,pfile_sizes):
        pfiles_trs = []
        for group in self.pfiles_by_func:
            set = []
            for ind in group:
                set.append(pfile_sizes[ind])
            pfiles_trs.append(set)
        return pfiles_trs
    
    def _lucas_3dtcat(self,pfiles_trs,spiral=True,suffix_out=''):
        for group,name in zip(pfiles_trs,self.dset_labels):
            catcmd = ['3dTcat','-prefix',name+suffix_out]
            for i,[pfile,ntr] in enumerate(group):
                if spiral:
                    shell_command(['sprlioadd','-0','-m','0',pfile,name+str(i),
                                   str(ntr),str(self.nslices)])
                general_cleaner(name+str(i),1)
                shell_command(['to3d','-epan','-prefix',name+str(i),
                               '-xFOV','120R-120L','-yFOV','120A-120P','-zSLAB',
                               str(self.isvalues[0])+'I-'+str(self.isvalues[1])+'S',
                               '-time:tz',str(ntr),str(self.nslices),str(self.tr_time)+'s',
                               'seqplus','3D:0:0:64:64:'+str(ntr*self.nslices)+':'+name+str(i)])
                general_cleaner(name+str(i),0)
                general_cleaner(name+str(i)+suffix_out,1)
                shell_command(['3dTcat','-prefix',name+str(i)+suffix_out,
                               name+str(i)+'orig['+str(self.leadin)+'..'+str(ntr+1-self.leadout)+']'])
                general_cleaner(name+str(i),1)
                catcmd.extend([name+str(i)+suffix_out+'+orig'])
            shell_command(catcmd)
        return suffix_out
    
      
    def _lucas_3dtshift(self,suffix_out='',suffix_in=''):
        for name in self.dset_labels:
            shell_command(['3dTshift','-slice','0','-prefix',name+suffix_out,name+suffix_in+'+orig'])
            general_cleaner(name+suffix_in,1)
        return suffix_out
        
    def commands(self):
        allpfiles = glob.glob('*.mag')
        pfile_sizes = self._parse_psizes(allpfiles,self.tr_bytes)
        if not len(self.dset_labels) == len(self.pfiles_by_func):
            print 'ERROR: functional name labels and pfiles by functional index do not match.\n'
        else:
            pfiles_trs = self._assign_pfiles(pfile_sizes)
            self.tcat_suffix = self._lucas_3dtcat(pfiles_trs,suffix_out=self.tcat_suffix)
            self.tshift_suffix = self._lucas_3dtshift(dset_labels,suffix_out=self.tshift_suffix,
                                                      suffix_in=self.tcat_suffix)

