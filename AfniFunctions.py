import os
import sys
import glob
import shutil
from pprint import pprint
from mono_utility import (general_cleaner, shell_command, parse_dirs)

class AfniFunctions:
    def __init__(self):
        pass
    
    
    def reconstruct_anat_cni(self,anat_name=[],raw_anat=[]):
        general_cleaner(anat_name,1)
        shell_command(['3dcopy',raw_anat,anat_name])
        return {'dset_out':anat_name+'+orig'}
    
    
    def reconstruct_anat_lucas(self,anat_name=[],rawdir_searchexp='./*/'):
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
        saginfo = self.__runto3d_lucas(saggitaldir,prefix=anat_name,keepfiles=True)
        axiinfo = self.__runto3d_lucas(axialdir,prefix='axialtemp',keepfiles=False)
        isvalues = self.__isparse_lucas(axiinfo)
        os.chdir(currentdir)
        return {'isvalues':isvalues,'dset_out':anat_name+'+orig'}
    
    
    def __runto3d_lucas(self,dicomdir,prefix='',keepfiles=True,dicomprefix='I*',movedir='../../'):
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
    
    
    def __isparse_lucas(self,headerinfo):
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
    
    
    def warp_anatomical(self,anat_name=[],talairach_path=[]):
        shell_command(['@auto_tlrc','-warp_orig_vol','-suffix','NONE','-base', \
                        talairach_path,'-input',anat_name+'+orig.'])
        return {'dset_out':anat_name+'+tlrc'}
    
    
    def reconstruct_funcs_cni(self,dset_names=[],raw_funcs=[],leadin=[],leadouts=[]):
        general_cleaner(dset_names,1)
        if len(raw_funcs) != len(dset_names):
            print('\nWARNING: Functional labels not equal to number of functionals.\n')
        else:
            for i,(name,raw) in enumerate(zip(dset_names,raw_funcs)):
                if type(raw) == type([]):
                    for j,nraw in enumerate(raw):
                        shell_command(['3dTcat','-prefix',name+str(j),nraw+'['+str(leadin)+'..'+str(leadouts[i][j])+']'])
                    cat = [(name+str(j)+'+orig') for j in range(len(raw))]
                    cmd = ['3dTcat','-prefix',name]
                    cmd = cmd.extend(cat)
                    shell_command(cmd)
                elif os.path.exists('./'+raw):
                    shell_command(['3dTcat','-prefix',name,raw+'['+str(leadin)+'..'+str(leadouts[i])+']'])
        return {'dset_out':[(x+'+orig') for x in dset_names],'suffix_out':''}
        
        
    def reconstruct_funcs_lucas(self,dset_names=[],pfiles_by_func=[],tr_bytes=[],
                                nslices=[],isvalues=[],tr_time=[],leadin=[],
                                leadout=[]):
        allpfiles = glob.glob('*.mag')
        pfile_sizes = self.__parse_psizes(allpfiles,tr_bytes)
        if not len(dset_names) == len(pfiles_by_func):
            print 'ERROR: functional name labels and pfiles by functional index do not match.\n'
        else:
            pfiles_trs = self.__assign_pfiles(pfile_sizes,pfiles_by_func)
            suffix1 = self.__lucas_3dtcat(pfiles_trs,dset_names,nslices,isvalues,tr_time,
                                leadin,leadout)
            suffix2 = self.__lucas_3dtshift(dset_names,suffix_in=suffix1)
        return {'dset_out':[(x+suffix2+'+orig') for x in dset_names],'pfiles_trs':pfiles_trs,
            'suffix_out':suffix2}
        
        
    def __parse_psizes(self,pfiles,tr_bytes):
        sizes = []
        for file in pfiles:
            size = shell_command(['du','-b',file],ioflag=1)
            size = size.strip(' \n\t')
            sizes.append([file,int(size[0])])
        # calculate TR from filesize + hardcoded bytes per TR:
        for i in range(len(sizes)):
            sizes[i][1] = int(math.floor(sizes[i][1]/tr_bytes))
        return sizes
    
    
    def __assign_pfiles(self,pfile_sizes,pfiles_by_func):
        pfiles_trs = []
        for group in pfiles_by_func:
            set = []
            for ind in group:
                set.append(pfile_sizes[ind])
            pfiles_trs.append(set)
        return pfiles_trs
    
    
    def __lucas_3dtcat(self,pfiles_trs,dset_names,nslices,isvalues,tr_time,leadin,
                       leadout,spiral=True,suffix_out='_crop'):
        for group,name in zip(pfiles_trs,dset_names):
            catcmd = ['3dTcat','-prefix',name+suffix_out]
            for i,[pfile,ntr] in enumerate(group):
                if spiral:
                    shell_command(['sprlioadd','-0','-m','0',pfile,name+str(i),\
                                   str(ntr),str(nslices)])
                general_cleaner(name+str(i),1)
                shell_command(['to3d','-epan','-prefix',name+str(i),\
                               '-xFOV','120R-120L','-yFOV','120A-120P',\
                               '-zSLAB',str(isvalues[0])+'I-'+str(isvalues[1])+'S',\
                               '-time:tz',str(ntr),str(nslices),str(tr_time)+'s',\
                               'seqplus','3D:0:0:64:64:'+str(ntr*nslices)+':'+name+str(i)])
                general_cleaner(name+str(i),0)
                general_cleaner(name+str(i)+suffix_out,1)
                shell_command(['3dTcat','-prefix',name+str(i)+suffix_out,\
                               name+str(i)+'orig['+str(leadin)+'..'+str(ntr+1-leadout)+']'])
                general_cleaner(name+str(i),1)
                catcmd.extend([name+str(i)+suffix_out+'+orig'])
            shell_command(catcmd)
        return suffix_out
    
    
    def __lucas_3dtshift(self,dset_names,suffix_out='_cropts',suffix_in='_crop'):
        for name in dset_names:
            shell_command(['3dTshift','-slice','0','-prefix',name+suffix_out,name+suffix_in+'+orig'])
            general_cleaner(name+suffix_in,1)
        return suffix_out
        
        
    def correct_motion(self,dset_names=[],motion_labels=[],suffix_out='m',suffix_in=''):
        if len(motion_labels) != len(dset_names):
            print('\nWARNING: Motion labels not equal to number of functionals.\n')
        else:
            for i,(label,epi) in enumerate(zip(motion_labels,dset_names)):
                # clean out motion files:
                general_cleaner(label,0)
                general_cleaner(epi+suffix_out,1)
                # run 3dvolreg for each functional:
                shell_command(['3dvolreg','-Fourier','-twopass','-prefix',epi+suffix_out,'-base',
                               '3','-dfile',label+'.1D',epi+suffix_in+'+orig'])
        return {'dset_out':[(x+suffix_out+'+orig') for x in dset_names],'suffix_out':suffix_out}
        
    
    def blur_functionals(self,dset_names=[],suffix_in='m',suffix_out='b',kernel=4):
        for epi in dset_names:
            general_cleaner(epi+suffix_out,1)
            shell_command(['3dmerge','-prefix',epi+suffix_out,'-1blur_fwhm',str(kernel),
                           '-doall',epi+suffix_in+'+orig'])
        return {'dset_out':[(x+suffix_out+'+orig') for x in dset_names],'suffix_out':suffix_out}
        
        
    def normalize_functionals(self,dset_names=[],suffix_in='b',suffix_out='n',calc_precision='float'):
        for i,epi in enumerate(dset_names):
            general_cleaner(epi+suffix_out,1)
            general_cleaner(epi+'_average',1)
            shell_command(['3dTstat','-prefix',epi+'_average',epi+suffix_in+'+orig'])
            shell_command(['3drefit','-abuc',epi+'_average+orig'])
            shell_command(['3dcalc','-datum',calc_precision,'-a',epi+suffix_in+'+orig',
                           '-b',epi+'_average+orig','-expr','((a-b)/b)*100',
                           '-prefix',epi+suffix_out])
        return {'dset_out':[(x+suffix_out+'+orig') for x in dset_names],'suffix_out':suffix_out}
        
        
    def highpass_filter(self,dset_names=[],suffix_in='n',suffix_out='f',highpass_val=.011):
        for i,epi in enumerate(dset_names):
            general_cleaner(epi+suffix_out,1)
            shell_command(['3dFourier','-prefix',epi+suffix_out,'-highpass',
                           str(highpass_val),epi+suffix_in+'+orig'])
        return {'dset_out':[(x+suffix_out+'+orig') for x in dset_names],'suffix_out':suffix_out}
        
        
    def warp_functionals(self,dset_names=[],suffix_in='f'):
        for i,epi in enumerate(dset_names):
            shell_command(['adwarp','-apar',self.anat_name+'+tlrc','-dpar',epi+suffix_in+'+orig', \
                             '-dxyz',str(self.talairach_dxyz)])
        return {'dset_out':[(x+suffix_in+'+tlrc') for x in dset_names],'suffix_out':suffix_out}
        
        
    def mask_warped_functionals(self,dset_names=[],scripts_dir=[],talairach_path=[],
                                talairach_dxyz=[],suffix_in='f',suffix_out='_masked'):
        currentdir = os.getcwd()
        for epi in dset_names:
            os.chdir('../'+scripts_dir)
            if not os.path.exists('./talairach_mask+tlrc.HEAD'):
                shutil.copy(talairach_path+'.HEAD','./'+talairach_path.split('/')[-1]+'.HEAD')
                shutil.copy(talairach_path+'.BRIK.gz','./'+talairach_path.split('/')[-1]+'.BRIK.gz')
                shell_command(['3dresample','-dxyz',str(talairach_dxyz),str(talairach_dxyz), \
                                 str(talairach_dxyz),'-prefix','talairach_resamp','-inset', \
                                 talairach_path.split('/')[-1]])
                shell_command(['3dAutomask','-prefix','talairach_mask','-clfrac','0.1','talairach_resamp+tlrc'])
                shell_command(['3dAFNItoNIFTI','-prefix','talairach_mask','talairach_mask+tlrc'])
            os.chdir(currentdir)
            general_cleaner(epi+suffix_out,1)
            shell_command(['3dcalc','-a',epi+suffix_in+'+tlrc','-b','../'+scripts_dir+'/talairach_mask+tlrc',
                           '-expr', 'a*step(b)','-prefix',epi+suffix_out])
            shell_command(['3dAFNItoNIFTI','-prefix',epi+suffix_out,epi+suffix_out+'+tlrc'])
        return {'dset_out':[(x+suffix_out+'tlrc') for x in dset_names],'suffix_out':suffix_out}
        
        
    def convert_dset_to_nifti(self,dset_in=[]):
        for dset in dset_in:
            shell_command(['3dAFNItoNIFTI','-prefix',dset[:-5],dset])
        return {'dset_out':[(x[:-5]+'.nii') for x in dset_in]}
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        