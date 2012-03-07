#!/usr/bin/env python

import os
import sys
import glob
import shutil
from pprint import pprint
from mono_utility import (general_cleaner, shell_command, parse_dirs)


class AfniProcess():
    def __init__(self):
        self.usage = 'No usage specified.\n'
        self.required_kwargs = []
        self.args_set_flag = False
        self.bash_script_out = None
        self.outputs = {}
     
    def _check_required_args(self):
        do_not_proceed_flag = False
        for argument in self.required_kwargs:
            if getattr(self,argument,None):
                pass
            else:
                print(argument+' in '+self.__class__.__name__+' is not set, or set to None.\n')
                do_not_proceed_flag = True
        if not do_not_proceed_flag:
            return True
        else:
            return False
    
    def set(self,**kwargs):
        for argument,value in kwargs.items():
            if not argument in self.required_kwargs():
                print(argument+' is not required for '+self.__class__.__name__+', but set regardless.\n')
            setattr(self,argument,value)
        return True
 
    def write_bash_to_file(self,filename):
        pass
            
    def commands(self):
        pass
    
    def query_outputs(self):
        pprint(self.outputs)
        return self.outputs
    
    def run(self):
        proceed = self._check_required_args()
        if proceed:
            self.commands()
            return self.outputs


class Reconstruct_Anat_CNI(AfniProcess):
    def __init__(self,anat_name=None,raw_anat=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['anat_name','raw_anat']
        self.anat_name = anat_name
        self.raw_anat = raw_anat
        self.outputs = {'dset_out':self.anat_name}
    
    def commands(self):
        general_cleaner(self.anat_name,1)
        shell_command(['3dcopy',self.raw_anat,self.anat_name])


class Reconstruct_Anat_Lucas(AfniProcess):
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
        self.outputs = {'isvalues':self.isvalues,'dset_out':self.anat_name}
    
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



class Warp_Anatomical(AfniProcess):
    def __init__(self,anat_name=None,talairach_path=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['anat_name','talairach_path']
        self.anat_name = anat_name
        self.talairach_path = talairach_path
        self.outputs = {'dset_out':self.anat_name}
    
    def commands(self):
        shell_command(['@auto_tlrc','-warp_orig_vol','-suffix','NONE','-base',
                       self.talairach_path,'-input',self.anat_name+'+orig'])
        

class Reconstruct_Funcs_CNI(AfniProcess):
    def __init__(self,dset_labels=None,raw_funcs=None,leadin=None,leadouts=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','raw_funcs','leadin','leadouts']
        self.dset_labels = dset_labels
        self.raw_funcs = raw_funcs
        self.leadin = leadin
        self.leadouts = leadouts
        self.suffix_out = ''
        self.outputs = {'dset_out':[x for x in self.dset_labels],'suffix_out':self.suffix_out}
        
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


class Reconstruct_Funcs_Lucas(AfniProcess):
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
        self.outputs = {'dset_out':[(x+self.tshift_suffix) for x in self.dset_labels],
            'suffix_out':self.tshift_suffix}
        
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
    
    def _lucas_3dtcat(self,pfiles_trs,spiral=True,suffix_out=self.tcat_suffix):
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
    
      
    def _lucas_3dtshift(self,suffix_out=self.tshift_suffix,suffix_in=self.tcat_suffix):
        for name in self.dset_labels:
            shell_command(['3dTshift','-slice','0','-prefix',name+suffix_out,name+suffix_in+'+orig'])
            general_cleaner(name+suffix_in,1)
        return suffix_out
        
    def command(self):
        allpfiles = glob.glob('*.mag')
        pfile_sizes = self._parse_psizes(allpfiles,self.tr_bytes)
        if not len(self.dset_labels) == len(self.pfiles_by_func):
            print 'ERROR: functional name labels and pfiles by functional index do not match.\n'
        else:
            pfiles_trs = self._assign_pfiles(pfile_sizes)
            self.tcat_suffix = self._lucas_3dtcat(pfiles_trs)
            self.tshift_suffix = self._lucas_3dtshift(dset_labels,suffix_in=self.tcat_suffix)



class Correct_Motion(AfniProcess):
    def __init__(self,dset_labels=None,motion_labels=None,suffix_in='',suffix_out='_m'):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','motion_labels','suffix_in','suffix_out']
        self.dset_labels = dset_labels
        self.motion_labels = motion_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.return_keys = ['dset_out','suffix_out','motion_files']
        
    def command(self):
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
        return {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],
            'suffix_out':self.suffix_out,'motion_files':[label for label in self.motion_labels]}

class Blur_Functionals(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_m',suffix_out='_mb',kernel=4):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','suffix_out','kernel']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix.out
        self.return_keys = ['dset_out','suffix_out']
        
    def command(self):
        for func in self.dset_labels:
            general_cleaner(func+self.suffix_out,1)
            shell_command(['3dmerge','-prefix',func+self.suffix_out,'-1blur_fwhm',str(self.kernel),
                           '-doall',func+self.suffix_in+'+orig'])
        return {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],'suffix_out':self.suffix_out}


class Normalize_Functionals(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_mb',suffix_out='_mbn',calc_precision='float'):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','suffix_out','calc_precision']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.calc_precision = calc_precision
        self.return_keys = ['dset_out','suffix_out']
        
    def command(self):
        for i,epi in enumerate(self.dset_labels):
            general_cleaner(epi+self.suffix_out,1)
            general_cleaner(epi+'_average',1)
            shell_command(['3dTstat','-prefix',epi+'_average',epi+self.suffix_in+'+orig'])
            shell_command(['3drefit','-abuc',epi+'_average+orig'])
            shell_command(['3dcalc','-datum',self.calc_precision,'-a',epi+self.suffix_in+'+orig',
                           '-b',epi+'_average+orig','-expr','((a-b)/b)*100',
                           '-prefix',epi+self.suffix_out])
        return {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],'suffix_out':self.suffix_out}


class Highpass_Filter(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_mbn',suffix_out='_mbnf',highpass_val=.011):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','suffix_out','highpass_val']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.suffix_out = suffix_out
        self.highpass_val = highpass_val
        self.return_keys = ['dset_out','suffix_out']
        
    def command(self):
        for i,epi in enumerate(self.dset_labels):
            general_cleaner(epi+self.suffix_out,1)
            shell_command(['3dFourier','-prefix',epi+self.suffix_out,'-highpass',
                           str(self.highpass_val),epi+self.suffix_in+'+orig'])
        return {'dset_out':[(x+self.suffix_out) for x in self.dset_labels],'suffix_out':self.suffix_out}


class Warp_Functionals(AfniProcess):
    def __init__(self,dset_labels=None,suffix_in='_mbnf',anat_name=None,talairach_dxyz=None):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','suffix_in','anat_name','talairach_dxyz']
        self.dset_labels = dset_labels
        self.suffix_in = suffix_in
        self.anat_name = anat_name
        self.talairach_dxyz = talairach_dxyz
        self.return_keys = ['dset_out','suffix_out']
        
    def command(self):
        for i,epi in enumerate(self.dset_labels):
            shell_command(['adwarp','-apar',self.anat_name+'+tlrc','-dpar',epi+self.suffix_in+'+orig', \
                             '-dxyz',str(self.talairach_dxyz)])
        return {'dset_out':[(x+self.suffix_in) for x in self.dset_labels],'suffix_out':self.suffix_in}
        
        
class Mask_Warped_Functionals(AfniProcess):
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
        self.return_keys = ['dset_out','suffix_out']
    
    def command(self):
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
        return {'dset_out':[(x+suffix_out) for x in dset_labels],'suffix_out':suffix_out}
        
        
class Convert_to_Nifti(AfniProcess):
    def __init__(self,dset_labels=None,afni_format='+tlrc'):
        AfniProcess.__init__(self)
        self.required_kwargs = ['dset_labels','afni_format']
        self.dset_labels = dset_labels
        self.afni_format = afni_format
        self.return_keys = ['dset_out']
        
    def command(self):
        for dset in self.dset_labels:
            shell_command(['3dAFNItoNIFTI','-prefix',dset,dset+self.afni_format])
        return {'dset_out':[(x+'.nii') for x in self.dset_labels]}

        
        
        
        
        
        
        
        
        
        
        
        