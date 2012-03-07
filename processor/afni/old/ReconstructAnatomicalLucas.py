#!/usr/bin/env python

from AfniProcess import AfniProcess


class ReconstructAnatomicalLucas(AfniProcess):
    def __init__(self,anat_name=None,rawdir_searchexp='./*/',dicomprefix='I*',
                 movedir='../../'):
        AfniProcess.__init__(self)
        self.required_kwargs = ['anat_name','rawdir_searchexp','dicomprefix',
                                'movedir']
        self.anat_name = anat_name
        self.rawdir_searchexp = rawdir_searchexp
        self.dicomprefix = dicomprefix
        self.movedir = movedir
        self.isvalues = None
    
    def output(self):
        self.outputs = {'isvalues':self.isvalues,'dset_out':self.anat_name}
        return self.outputs
    
    def _runto3d_lucas(self,dicomdir,prefix='',keepfiles=True):
        basedir = os.getcwd()
        os.chdir(dicomdir)
        if not prefix: print 'ERROR: no prefix specified. Will now crash...\n'
        general_cleaner(prefix,1)
        shell_command(['to3d','-prefix',prefix,self.dicomprefix])
        headerinfo = shell_command(['3dinfo',prefix+'+orig'],ioflag=1)
        if keepfiles:
            shutil.move(prefix+'+orig.HEAD',self.movedir)
            shutil.move(prefix+'+orig.BRIK',self.movedir)
        else:
            general_cleaner(prefix,1)
        os.chdir(basedir)
        return headerinfo   
    
    def _isparse_lucas(self,headerinfo):
        isline = []
        isstrip = []
        hlist = headerinfo.split('\n')
        for item in hlist:
            if item.find('I-to-S') != -1:
                isline = item.split(' ')
        for segment in isline:
            if len(segment) != 0:
                isstrip.append(segment)
        return [abs(eval(isstrip[2])),abs(eval(isstrip[5]))]
    
    def commands(self):
        currentdir = os.getcwd()
        rawdir = glob.glob(self.rawdir_searchexp)[0]
        os.chdir(rawdir)
        dicomdirs = glob.glob('./*/')
        axialdir,saggitaldir = [],[]
        for dir in dicomdirs:
            os.chdir(dir)
            dicomfiles = glob.glob('./*')
            if len(files) == 24: axialdir = dir
            if len(files) == 116: saggitaldir = dir
            os.chdir('../')
        saginfo = self._runto3d_lucas(saggitaldir,prefix=self.anat_name,keepfiles=True)
        axiinfo = self._runto3d_lucas(axialdir,prefix='axialtemp',keepfiles=False)
        self.isvalues = self._isparse_lucas(axiinfo)
        os.chdir(currentdir)