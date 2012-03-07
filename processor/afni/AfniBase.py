#!/usr/bin/env python

from AfniProcess import AfniProcess

from PyAfni import *

from ..utilities.shell_command import shell_command
from ..utilities.general_cleaner import general_cleaner
from ..utilities.parse_dirs import parse_dirs

class BlurFunctional(AfniProcess):
    def __init__(self, dset=None, format='+orig', suffix_out='b', kernel=4):
        AfniProcess.__init__(self)
        self.dset = dset
        self.suffix_out = suffix_out
        self.kernel = kernel
        self.format = format
        
    
    def commands(self,writeout=False):
        cleancmd = general_cleaner(self.dset+self.suffix_out,afni=True,writeout=writeout)
        merge = Py3dMerge(prefix = self.dset+self.suffix_out,
                          blur_kernel = self.kernel,
                          input = self.dset+self.format)
        if writeout:
            self.whitebox = ['#* Blur Functionals:']
            mergecmd = merge.whitebox()
            self._whitebox_extend(cleancmd,mergecmd)
        else:
            merge.run()




class ConvertToNifti(AfniProcess):
    def __init__(self, dset=None, format='+tlrc'):
        AfniProcess.__init__(self)
        self.dset = dset
        self.format = format


    def commands(self,writeout=False):
        afnitonifti = Py3dAFNItoNIFTI(prefix = self.dset,
                                      input = self.dset+self.format)
        if writeout:
            self.whitebox = ['#* Convert from AFNI to Nifti:']
            cmd = afnitonifti.whitebox()
            self._whitebox_extend(cmd)
        else:
            afnitonifti.run()
            



            
class CorrectMotion(AfniProcess):
    def __init__(self,dset=None, format='+orig', motionlabel=None, suffix_out='_m'):
        AfniProcess.__init__(self)
        self.dset= dset
        self.motionlabel = motionlabel
        self.suffix_out = suffix_out
        self.format = format
        
        
    def commands(self,writeout=False):
        clean_1D = general_cleaner(self.motionlabel,afni=False,writeout=writeout)
        clean_afni = general_cleaner(self.dset+self.suffix_out,afni=True,writeout=writeout)
        
        volreg = Py3dvolreg(prefix=self.dset+self.suffix_out,
                            dfile=self.motionlabel,
                            input=self.dset+self.format)
        if writeout:
            self.whitebox = ['#* Motion Correction:']
            volcmd = volreg.whitebox()
            self._whitebox_extend(clean_1D,clean_afni,volcmd)
        else:
            volcmd.run()

             
             
                
                
class HighpassFilter(AfniProcess):
    def __init__(self,dset=None, format='+orig', suffix_out='f',
                 highpass_val=.011):
        AfniProcess.__init__(self)
        self.dset = dset
        self.format = format
        self.suffix_out = suffix_out
        self.highpass_val = highpass_val
        

    def commands(self,writeout=False):
        clean = general_cleaner(self.dset+self.suffix_out,afni=True,writeout=writeout)
        
        fourier = Py3dFourier(prefix=self.dset+self.suffix_out,
                              input=self.dset+self.format,
                              highpass=self.highpass_val)
        
        if writeout:
            self.whitebox = ['#* Highpass Filter:']
            fcmd = fourier.whitebox()
            self._whitebox_extend(clean,fcmd)
        else:
            fourier.run()
            
         
                
                
## THIS ONE LIKELY DOESNT WORK AND LIKELY ISNT THAT USEFUL:          
'''
class MaskWarpedFunctional(AfniProcess):
    def __init__(self, dset=None, mask_dir=None, talaiarach_dset_files=[],
                 suffix_out='_masked', talairach_dxyz=None,
                 mask_name='talairach_mask+tlrc'):
        AfniProcess.__init__(self)
        self.dset = dset
        self.mask_dir = mask_dir
        self.mask_name = mask_name
        self.talairach_files = talairach_dset_files
        self.suffix_out = suffix_out
        self.dxyz = talairach_dxyz
        
    
    def commands(self):

        mask_exists = glob.glob(os.path.join(self.mask_dir,self.mask_name)+'*')
        
        if not mask_exists:
            if isinstance(self.talairach_files,(list,tuple)):
                for file in self.talairach_files:
                    shutil.copy(file,self.mask_dir)
            else:
                shutil.copy(self.talairach_files,self.mask_dir)
            
            resample = Py3dresample(dxyz=self.dxyz, prefix='talairach_resamp',
                                    inset=os.path.join(self.mask_dir,self.talairach_files.split('/')[-1]))
            
            automask = Py3dAutomask(prefix=os.path.join(self.mask_dir,mask_name),
                                    clfrac=0.1, input='talairach_resamp+tlrc')
            
            aftonif = Py3dAFNItoNIFTI(prefix=os.path.join(self.mask_dir,self.mask_name.strip('+tlrc')),
                                      input=os.path.join(self.mask_dir,self.mask_name))
            
            resample.run()
            automask.run()
            aftonif.run()
            
        general_cleaner(self.dset+self.suffix_out,afni=True)
        
        calc = Py3dcalc(a=self.dset+'tlrc', b=os.path.join(self.mask_dir,self.mask_name),
                        expr='a*step(b)', prefix=self.dset+self.suffix_out)
        
        aftonif2 = Py3dAFNItoNIFTI(prefix=self.dset+self.suffix_out,
                                   input=self.dset+self.suffix_out+'+tlrc')
        
        calc.run()
        aftonif2.run()
            
'''           
                
                
class NormalizeFunctional(AfniProcess):
    def __init__(self, dset=None, format='+orig', suffix_out='n', calc_precision='float',
                 average_dset=None, average_format='+orig'):
        AfniProcess.__init__(self)
        self.dset = dset
        self.format = format
        self.suffix_out = suffix_out
        self.calc_precision = calc_precision
        self.average_dset = average_dset
        self.average_format = average_format
        
    
    def commands(self,writeout=False):
        
        if not self.average_dset:
            self.average_dset = self.dset
            self.average_format = self.format

        
        cleandset = general_cleaner(self.dset+self.suffix_out, afni=True,writeout=writeout)
        cleanavg = general_cleaner(self.average_dset+'_average',afni=True,writeout=writeout)
        
        print self.dset
        print format
        
        tstat = Py3dTstat(prefix=self.average_dset+'_average',
                          input=self.average_dset+self.average_format)
        
        refit = Py3drefit(input=self.average_dset+'_average'+self.average_format)
        
        calc = Py3dcalc(datum=self.calc_precision, a=self.dset+self.format,
                        b=self.average_dset+'_average'+self.average_format,
                        expr='((a-b)/b)*100',
                        prefix=self.dset+self.suffix_out)
        
        if writeout:
            self.whitebox = ['#* Normalize functional data:']
            tstatcmd = tstat.whitebox()
            refitcmd = refit.whitebox()
            calccmd = calc.whitebox()
            self._whitebox_extend(cleandset,cleanavg,tstatcmd,refitcmd,calccmd)
        else:
            tstat.run()
            refit.run()
            calc.run()
        
                
                
                
class ReconstructAnatomicalCNI(AfniProcess):
    def __init__(self, anat_name=None, raw_anat=None):
        AfniProcess.__init__(self)
        self.anat_name = anat_name
        self.raw_anat = raw_anat


    def commands(self,writeout=True):
        clean = general_cleaner(self.anat_name,afni=True,writeout=writeout)
        copy = Py3dcopy(input=self.raw_anat, output=self.anat_name)
        
        if writeout:
            self.whitebox = ['#* Reconstruct anatomicals:']
            copycmd = copy.whitebox()
            self._whitebox_extend(clean,copycmd)
        else:
            copy.run()
                

'''
class ReconstructAnatomicalLucas(AfniProcess):
    def __init__(self,anat_name=None,rawdir_searchexp='*/',dicomprefix='I*',
                 subject_top_dir=None):
        AfniProcess.__init__(self)
        self.anat_name = anat_name
        self.rawdir_searchexp = rawdir_searchexp
        self.dicomprefix = dicomprefix
        self.movedir = subject_top_dir
        self.isvalues = None
    
    
    def _runto3d_lucas(self,dicomdir,prefix=None,keepfiles=True):
        if not prefix:
            print 'ERROR: no prefix specified. Will now crash...\n'
            
        general_cleaner(os.path.join(dicomdir,prefix),afni=True)
        
        to3d = Pyto3d(prefix=os.path.join(self.movedir,prefix),
                      input=os.path.join(dicomdir,self.dicomprefix))
        to3d.run()
        
        info = Py3dinfo(input=os.path.join(self.movedir,prefix+'+orig'))
        headerinfo = info.run()
        
        if not keepfiles:
            general_cleaner(os.path.join(self.movedir,prefix),afni=True)

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
        rawdir = glob.glob(os.path.join(self.topdir,self.rawdir_searchexp))[0]
        dicomdirs = glob.glob(os.path.join(rawdir,'*/'))
        axialdir,saggitaldir = [],[]
        
        for dir in dicomdirs:
            dicomfiles = glob.glob(dir+'*')
            if len(dicomfiles) == 24: axialdir = dir
            if len(dicomfiles) == 116: saggitaldir = dir

        saginfo = self._runto3d_lucas(saggitaldir,prefix=self.anat_name,keepfiles=True)
        axiinfo = self._runto3d_lucas(axialdir,prefix='axialtemp',keepfiles=False)
        
        self.isvalues = self._isparse_lucas(axiinfo)
'''             


class ReconstructFunctionalCNI(AfniProcess):
    def __init__(self,dset=None, raw_funcs=None, leadin=None, leadout=None):
        AfniProcess.__init__(self)
        self.dset = dset
        self.raw_funcs = raw_funcs
        self.leadin = leadin
        self.leadout = leadout
        
        
    def commands(self,writeout=False):
        clean = general_cleaner(self.dset,afni=True,writeout=writeout)
        tcat = Py3dTcat(prefix=self.dset,
                        input=self.raw_funcs, leadin=self.leadin, leadout=self.leadout)
        
        if writeout:
            self.whitebox = ['#* Reconstruct functionals:']
            tcatcmd = tcat.whitebox()
            self._whitebox_extend(clean,tcatcmd)
        else:
            tcat.run()
        
        
                

##### UNDER CONSTRUCTION ###### ::
'''
class ReconstructFunctionalLucas(AfniProcess):
    def __init__(self, dset=None, pfiles=None, tr_bytes=393216,
                 nslices=None, isvalues=None, tr_time=None, leadin=None,
                 leadout=None, subject_dir=None):
        AfniProcess.__init__(self)
        self.dset = dset
        self.topdir = subject_dir
        self.pfiles = pfiles
        self.tr_bytes = tr_bytes
        self.nslices = nslices
        self.isvalues = isvalues
        self.tr_time = tr_time
        self.leadin = leadin
        self.leadout = leadout
        self.tcat_suffix = '_crop'
        self.tshift_suffix = '_cropts'
        
        
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
    
    
    def _lucas_3dtcat(self,pfiles_trs,spiral=True,suffix_out=None):
        
        partial_dsets = []
        for i,[pfile,ntr] in enumerate(pfiles_trs):
            if spiral:
                shell_command(['sprlioadd','-0','-m','0',pfile,self.dset+str(i),
                               str(ntr),str(self.nslices)])
                
            general_cleaner(self.dset+str(i),afni=True)
            
            shell_command(['to3d','-epan','-prefix',self.dset+str(i),
                           '-xFOV','120R-120L','-yFOV','120A-120P','-zSLAB',
                           str(self.isvalues[0])+'I-'+str(self.isvalues[1])+'S',
                           '-time:tz',str(ntr),str(self.nslices),str(self.tr_time)+'s',
                           'seqplus','3D:0:0:64:64:'+str(ntr*self.nslices)+':'+self.dset+str(i)])
            
            partial_dsets.append(self.dset+str(i)+'+orig')
            
        general_cleaner(self.dset+self.suffix_out,afni=True)
        
        tcat = Py3dTcat(prefix=self.dset+suffix_out,
                        input=partial_dsets, leadin=self.leadin, leadout=self.leadout)
        
        general_cleaner(self.dset+str(i),afni=True)
        
    
      
    def _lucas_3dtshift(self,suffix_out='',suffix_in=''):
        
        tshift = Py3dTshift(slice=0, prefix=self.dset+suffix_out,
                            input=self.dset+suffix_in+'+orig')
        tshift.run()
        general_cleaner(self.dset+suffix_in,afni=True)
        
    
    def commands(self):
        allpfiles = glob.glob(os.path.join(self.topdir,'*.mag'))
        pfile_sizes = self._parse_psizes(allpfiles,self.tr_bytes)

        self._lucas_3dtcat(pfile_sizes,suffix_out=self.tcat_suffix)
        self._lucas_3dtshift(dset_labels,suffix_out=self.tshift_suffix,
                             suffix_in=self.tcat_suffix)        
'''                



class WarpAnatomical(AfniProcess):
    def __init__(self, anat_name=None, talairach_path=None):
        AfniProcess.__init__(self)
        self.anat_name = anat_name
        self.talairach_path = talairach_path
        
        
    def commands(self,writeout=False):
        autot = PyAutoTalairach(warp_orig_vol=True, suffix='NONE',
                                base=self.talairach_path,
                                input=self.anat_name+'+orig')
        
        if writeout:
            self.whitebox = ['#* Warp anatomical:']
            warpcmd = autot.whitebox()
            self._whitebox_extend(warpcmd)
        else:
            autot.run()
                


class WarpFunctional(AfniProcess):
    def __init__(self,dset=None, anat_name=None, talairach_dxyz=None):
        AfniProcess.__init__(self)
        self.dset = dset
        self.anat_name = anat_name
        self.dxyz = talairach_dxyz
        

    def commands(self,writeout=False):
        adwarp = Pyadwarp(apar=self.anat_name+'+tlrc',
                          dpar=self.dset+'+orig',
                          dxyz=self.dxyz)
        
        if writeout:
            self.whitebox = ['#* Warp functional:']
            warpcmd = adwarp.whitebox()
            self._whitebox_extend(warpcmd)
        else:
            adwarp.run()
        
                
                
                
                
                
                
                