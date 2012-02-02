#!/usr/bin/env python

# imports:
import os
import sys
import glob
import shutil
import subprocess
from pprint import pprint
from mono_utility import (general_cleaner, shell_command)



'''
1.11.11     Kiefer Katovich


'''


class Preprocessor:
    def __init__(self,data_type='cni'):
        # required variables, initialized to empty for starts:
        self.data_type = data_type
        if self.data_type == 'cni':
            self.required_vars = ['anat_name','func_names',\
                                  'motion_labels','outdir','trs','nslices','tr_time',\
                                  'trxslices','leadin','leadouts','scripts_dir',\
                                  'talairach_path','leadout']
            self.optional_vars = ['raw_anat','raw_funcs','raw_funcs_alt']
        elif self.data_type == 'lucas':
            self.required_vars = ['leadin','leadout','talairach_path','scripts_dir',\
                                  'tr_time','outdir','func_names','anat_name',\
                                  'pfiles_by_func','tr_bytes','nslices']
            self.optional_vars = []
        else:
            print 'ERROR: data_type keyword argument must be cni or lucas.\n\n'
        
        # do tags, for run specifications:
        self.do_anat_reconstruction = True
        self.do_func_reconstruction = True
        self.do_warp_anatomical = True
        self.do_correct_motion = True
        self.do_normalize = True
        self.do_highpass_filter = True
        self.do_warp_functionals = True
        self.do_mask_functionals = True
        self.do_convert_to_nifti = True
        
        # completion tags:
        self.initialized_variables = False
        self.reconstructed_anat = False
        self.reconstructed_funcs = False
        self.warped_anatomical = False
        self.corrected_motion = False
        self.normalized = False
        self.highpass_filtered = False
        self.warped_functionals = False
        self.masked = False
        self.converted_to_nifti = False
        
    def initialize_variables(self,var_dict,flags=False):
        self.var_dict = var_dict
        if flags:
            for key, value in flags.items():
                setattr(self,key,value)
        for key, value in var_dict.items():
            setattr(self,key,value)
        for var_name in self.required_vars:
            if not var_name in var_dict:
                print 'WARNING: %s was NOT included in the variable dictionary!\n' % var_name
                print 'Not including %s may or may not break the pipeline.\n' % var_name
                print 'Know what you are doing!\n'
                setattr(self,var_name,False)
        for var_name in self.optional_vars:
            if not var_name in var_dict:
                setattr(self,var_name,False)
        if self.data_type == 'lucas':
            # determine if the user has specified TRs:
            if 'trs' in self.var_dict:
                setattr(self,'trs',self.var_dict['trs'])
            else:
                setattr(self,'trs',0)
        self.initialized_variables = True
    
    def __runto3d(self,dicomdir,prefix='',keepfiles=True,dicomprefix='I*',movedir='../../'):
        basedir = os.getcwd()
        os.chdir(dicomdir)
        if not prefix: print 'ERROR: no prefix specified. Will now crash...\n'
        general_cleaner(prefix,1)
        shell_command(['to3d','-prefix',prefix,dicomprefix])
        headerinfo = shell_command(['3dinfo',prefix+'+orig'],ioflag=1)
        if keepfiles:
            shutil.move(prefix+'+orig.HEAD',movedir)
            shutil.move(prefix+'+orig.BRIK',movedir)
        else:
            general_cleaner(prefix,1)
        os.chdir(basedir)
        return headerinfo
    
    def __isparse(self,headerinfo):
        isline = []
        isstrip = []
        hlist = headerinfo.split('\n')
        for item in hlist:
            if item.find('I-to-S') != -1:
                isline = item.split(' ')
        for segment in isline:
            if len(segment) != 0:
                isstrip.append(segment)
        setattr(self,'isvalues',[abs(eval(isstrip[2])),abs(eval(isstrip[5]))])
        
    def __cni_find_raws(self,scan_nums):
        raw_names = []
        nii_files_zipped = glob.glob('*.nii.gz')
        nii_num_pairs = []
        for nii in nii_files_zipped:
            scan_num = int((nii.split('_'))[0])
            nii_num_pairs.append([nii,scan_num])
        for num in scan_nums:
            if type(num) == type([]):
                raw_block = []
                for sub_num in num:
                    for pair in nii_num_pairs:
                        if pair[1] == sub_num:
                            raw_block.append(pair[0])
                raw_names.append(raw_block)
            else:
                for pair in nii_num_pairs:
                    if pair[1] == num:
                        raw_names.append(pair[0])
            #if scan_num in scan_nums:
            #    raw_names.append(nii)
        return raw_names
    
    def reconstruct_anat(self,rawdir_searchexp='./*/'):
        if self.data_type == 'cni':
            general_cleaner(self.anat_name,1)
            # create afni anat from nifti:
            if not self.raw_anat:
                self.raw_anat = self.__cni_find_raws([self.anat_scan_num])[0]
            shell_command(['3dcopy',self.raw_anat,self.anat_name])
        elif self.data_type == 'lucas':
            # guess the rawdir based on the search expression.
            # the default is the first directory in the subject directory... (typically works!)
            currentdir = os.getcwd()
            rawdir = glob.glob(rawdir_searchexp)[0]
            os.chdir(rawdir)
            dicomdirs = glob.glob('./*/')
            axialdir,saggitaldir = [],[]
            for dir in dicomdirs:
                os.chdir(dir)
                dicomfiles = glob.glob('./*')
                if len(files) == 24: axialdir = dir
                if len(files) == 116: saggitaldir = dir
                os.chdir('../')
            saginfo = self.__runto3d(saggitaldir,prefix=self.anat_name,keepfiles=True)
            axiinfo = self.__runto3d(axialdir,prefix='axialtemp',keepfiles=False)
            self.__isparse(axiinfo)
            os.chdir(currentdir)
        self.reconstructed_anat = True
    
    def warp_anatomical(self):
        # tailarach warp that sucker:
        shell_command(['@auto_tlrc','-warp_orig_vol','-suffix','NONE','-base', \
                        self.talairach_path,'-input',self.anat_name+'+orig.'])
        self.warped_anatomical = True
        
       
    def __parse_psizes(self,pfiles):
        sizes = []
        for file in pfiles:
            size = shell_command(['du','-b',file],ioflag=1)
            size = size.strip(' \n\t')
            sizes.append([file,int(size[0])])
        # calculate TR from filesize + hardcoded bytes per TR:
        for i in range(len(sizes)):
            sizes[i][1] = int(math.floor(sizes[i][1]/self.tr_bytes))
        return sizes
    
    def __assign_pfiles(self,pfile_sizes):
        pfiles_trs = []
        for group in self.pfiles_by_func:
            set = []
            for ind in group:
                set.append(pfile_sizes[ind])
            pfiles_trs.append(set)
        return pfiles_trs
    
    def __lucas_3dtcat(self,spiral=True,suffix_out='_crop'):
        for group,name in zip(self.pfiles_trs,self.func_names):
            catcmd = ['3dTcat','-prefix',name+suffix_out]
            for i,[pfile,ntr] in enumerate(group):
                if spiral:
                    shell_command(['sprlioadd','-0','-m','0',pfile,name+str(i),\
                                   str(ntr),str(self.nslices)])
                general_cleaner(name+str(i),1)
                shell_command(['to3d','-epan','-prefix',name+str(i),\
                               '-xFOV','120R-120L','-yFOV','120A-120P',\
                               '-zSLAB',str(self.isvalues[0])+'I-'+str(self.isvalues[1])+'S',\
                               '-time:tz',str(ntr),str(self.nslices),str(self.tr_time)+'s',\
                               'seqplus','3D:0:0:64:64:'+str(ntr*self.nslices)+':'+name+str(i)])
                general_cleaner(name+str(i),0)
                general_cleaner(name+str(i)+suffix_out,1)
                shell_command(['3dTcat','-prefix',name+str(i)+suffix_out,\
                               name+str(i)+'orig['+str(self.leadin)+'..'+str(ntr+1-self.leadout)+']'])
                general_cleaner(name+str(i),1)
                catcmd.extend([name+str(i)+suffix_out+'+orig'])
            shell_command(catcmd)
        return suffix_out
    
    def __lucas_3dtshift(self,suffix_out='_cropts',suffix_in='_crop'):
        for name in self.func_names:
            shell_command(['3dTshift','-slice','0','-prefix',name+suffix_out,name+suffix_in+'+orig'])
            general_cleaner(name+suffix_in,1)
        return True
    
    def reconstruct_funcs(self):
        general_cleaner(self.func_names,1)
        if self.data_type == 'cni':
            if not self.raw_funcs:
                self.raw_funcs = self.__cni_find_raws(self.func_scan_nums)
                pprint(self.raw_funcs)
            if len(self.raw_funcs) != len(self.func_names):
                print('\nWARNING: Functional labels not equal to number of functionals.\n')
            else:
                for i,(name,raw) in enumerate(zip(self.func_names,self.raw_funcs)):
                    if type(raw) == type([]):
                        for j,nraw in enumerate(raw):
                            shell_command(['3dTcat','-prefix',name+str(j),nraw+'['+str(self.leadin)+'..'+str(self.leadouts[i][j])+']'])
                        cat = [(name+str(j)+'+orig') for j in range(len(raw))]
                        cmd = ['3dTcat','-prefix',name]
                        cmd = cmd.extend(cat)
                        shell_command(cmd)
                    elif os.path.exists('./'+raw):
                        shell_command(['3dTcat','-prefix',name,raw+'['+str(self.leadin)+'..'+str(self.leadouts[i])+']'])
                    elif self.raw_funcs_alt:
                        cur_alt = self.raw_funcs_alt[i]
                        if os.path.exists('./'+cur_alt):
                            shell_command(['3dTcat','-prefix',name,cur_alt+'['+str(self.leadin)+'..'+str(self.leadouts[i])+']'])
                        else:
                            print 'ERROR: No alternate found, original not found.\n'
                    else:
                        print 'ERROR: original raw not found, no alternates defined.\n'
        elif self.data_type == 'lucas':
            allpfiles = glob.glob('*.mag')
            pfile_sizes = self.__parse_psizes(allpfiles)
            if not len(self.func_names) == len(self.pfiles_by_func):
                print 'ERROR: functional name labels and pfiles by functional index do not match.\n'
            else:
                pfiles_trs = self.__assign_pfiles(self,pfile_sizes)
                setattr(self,'pfiles_trs',pfiles_trs)
                self.__lucas_3dtcat()
                self.__lucas_3dtshift()
        self.reconstructed_funcs = True
        
    def correct_motion(self,suffix_out='m',suffix_in=''):
        # ensure motion labels and functionals match:
        if len(self.motion_labels) != len(self.func_names):
            print('\nWARNING: Motion labels not equal to number of functionals.\n')
        else:
            for i,(label,epi) in enumerate(zip(self.motion_labels,self.func_names)):
                # clean out motion files:
                general_cleaner(label,0)
                general_cleaner(epi+suffix_out,1)
                # run 3dvolreg for each functional:
                shell_command(['3dvolreg','-Fourier','-twopass','-prefix',epi+suffix_out,'-base', \
                                 '3','-dfile',label+'.1D',epi+suffix_in+'+orig'])
        self.corrected_motion = True
        return suffix_out
    
    def normalize(self,suffix_in='m',suffix_out='n',calc_precision='float'):
        for i,epi in enumerate(self.func_names):
            general_cleaner(epi+suffix_out,1)
            general_cleaner(epi+'_average',1)
            shell_command(['3dTstat','-prefix',epi+'_average',epi+suffix_in+'+orig'])
            shell_command(['3drefit','-abuc',epi+'_average+orig'])
            shell_command(['3dcalc','-datum',calc_precision,'-a',epi+suffix_in+'+orig',
                           '-b',epi+'_average+orig','-expr','((a-b)/b)*100',
                           '-prefix',epi+suffix_out])
        self.normalized = True
        return suffix_out
    
    def highpass_filter(self,suffix_in='n',suffix_out='f',highpass_val=.011):
        for i,epi in enumerate(self.func_names):
            general_cleaner(epi+suffix_out,1)
            shell_command(['3dFourier','-prefix',epi+suffix_out,'-highpass',
                           str(highpass_val),epi+suffix_in+'+orig'])
        self.highpass_filtered = True
        return suffix_out
    
    def warp_functionals(self,suffix_in='f'):
        for i,epi in enumerate(self.func_names):
            shell_command(['adwarp','-apar',self.anat_name+'+tlrc','-dpar',epi+suffix_in+'+orig', \
                             '-dxyz',str(self.talairach_dxyz)])
        self.warped_functionals = True
        return suffix_in
    
    def mask(self,suffix_in='f',suffix_out='_masked'):
        print os.getcwd()
        currentdir = os.getcwd()
        for epi in self.func_names:
            os.chdir('../'+self.scripts_dir)
            if not os.path.exists('./talairach_mask+tlrc.HEAD'):
                shutil.copy(self.talairach_path+'.HEAD','./'+self.talairach_path.split('/')[-1]+'.HEAD')
                shutil.copy(self.talairach_path+'.BRIK.gz','./'+self.talairach_path.split('/')[-1]+'.BRIK.gz')
                shell_command(['3dresample','-dxyz',str(self.talairach_dxyz),str(self.talairach_dxyz), \
                                 str(self.talairach_dxyz),'-prefix','talairach_resamp','-inset', \
                                 self.talairach_path.split('/')[-1]])
                shell_command(['3dAutomask','-prefix','talairach_mask','-clfrac','0.1','talairach_resamp+tlrc'])
                shell_command(['3dAFNItoNIFTI','-prefix','talairach_mask','talairach_mask+tlrc'])
            os.chdir(currentdir)
            general_cleaner(epi+suffix_out,1)
            shell_command(['3dcalc','-a',epi+suffix_in+'+tlrc','-b','../'+self.scripts_dir+'/talairach_mask+tlrc', \
                             '-expr', 'a*step(b)','-prefix',epi+suffix_out])
            shell_command(['3dAFNItoNIFTI','-prefix',epi+suffix_out,epi+suffix_out+'+tlrc'])
        self.masked = True
        return suffix_out
    
    def convert_to_nifti(self,suffix_in='_masked',suffix_out='_masked',orig=False):
        for epi in self.func_names:
            if not orig:
                shell_command(['3dAFNItoNIFTI','-prefix',epi+suffix_in,epi+suffix_out+'+tlrc'])
            else:
                shell_command(['3dAFNItoNIFTI','-prefix',epi+suffix_in,epi+suffix_out+'+orig'])
        self.converted_to_nifti = True
        return suffix_out
    
    def run(self):
        if self.initialized_variables:
            if self.do_anat_reconstruction == True:
                self.reconstruct_anat()
            if self.do_func_reconstruction == True:
                self.reconstruct_funcs()
            if self.do_warp_anatomical == True:
                self.warp_anatomical()
            if self.do_correct_motion == True:
                self.correct_motion()
            if self.do_normalize == True:
                self.normalize()
            if self.do_highpass_filter == True:
                self.highpass_filter()
            if self.do_warp_functionals == True:
                self.warp_functionals()
            if self.do_mask_functionals == True:
                self.mask()
            if self.do_convert_to_nifti == True:
                self.convert_to_nifti()
            
        

            
    
        