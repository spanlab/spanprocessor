#!/usr/bin/env python

import os

from ..utilities.shell_command import shell_command
from ..utilities.general_cleaner import general_cleaner

class AfniFunction(object):
    def __init__(self):
        self.shell = False
        self.ioflag = False
        
    @property
    def command(self):
        cmd = [self.assignments['$function']]
        input = []
        output = []
        for key,value in self.assignments.items():
            if isinstance(value,(list,tuple)):
                if key == '$output':
                    for val in value:
                        if val:
                            output.append(str(val))
                elif key == '$input':
                    for val in value:
                        if val:
                            input.append(str(val))
                elif key == '$function':
                    pass
                else:
                    cmd.append(key)
                    for val in value:
                        if val:
                            cmd.append(str(val))
            else:
                if key == '$output':
                    if value:
                        output.append(str(value))
                elif key == '$input':
                    if value:
                        input.append(str(value))
                elif key == '$function':
                    pass
                else:
                    cmd.append(key)
                    if value:
                        cmd.append(str(value))
        if input:
            cmd.extend(input)
        if output:
            cmd.extend(output)
        return cmd
        
    def whitebox(self):
        print self.command
        return [' '.join(self.command)]
        
    def run(self):
        return shell_command(self.command,ioflag=self.ioflag,shell=self.shell)
                
                
                
class Py3dMerge(AfniFunction):
    def __init__(self,prefix=None,blur_kernel=None,doall=True,input=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.blur_kernel = blur_kernel
        self.doall = doall
        self.input = input
    
    @property
    def assignments(self):
        vars = {'$function':'3dmerge'}
        vars['-prefix'] = self.prefix
        vars['-1blur_fwhm'] = self.blur_kernel
        if self.doall:
            vars['-doall'] = ''
        vars['$input'] = self.input
        return vars
    
        
        
class Py3dAFNItoNIFTI(AfniFunction):
    def __init__(self, prefix=None, input=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.input = input

    @property
    def assignments(self):
        vars = {'$function':'3dAFNItoNIFTI'}
        vars['-prefix'] = self.prefix
        vars['$input'] = self.input
        return vars        

            
        
class Py3dvolreg(AfniFunction):
    def __init__(self, fourier=True, twopass=True, prefix=None, base=3,
                 dfile=None, input=None):
        AfniFunction.__init__(self)
        self.fourier = fourier
        self.twopass = twopass
        self.prefix = prefix
        self.base = base
        self.dfile = dfile
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'3dvolreg'}
        if self.fourier:
            vars['-Fourier'] = ''
        if self.twopass:
            vars['-twopass'] = ''
        vars['-prefix'] = self.prefix
        vars['-base'] = self.base
        vars['-dfile'] = self.dfile
        vars['$input'] = self.input
        return vars
        
        

class Py3dFourier(AfniFunction):
    def __init__(self, prefix=None, highpass=0.011, input=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.highpass = highpass
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'3dFourier'}
        vars['-prefix'] = self.prefix
        vars['-highpass'] = self.highpass
        vars['$input'] = self.input
        return vars
        
        

class Py3dresample(AfniFunction):
    def __init__(self, dxyz=None, prefix=None, inset=None):
        AfniFunction.__init__(self)
        self.dxyz = dxyz
        self.prefix = prefix
        self.inset = inset
        
    @property
    def assignments(self):
        vars = {'$function':'3dresample'}
        vars['-dxyz'] = self.dxyz
        vars['-prefix'] = self.prefix
        vars['-inset'] = self.inset
        return vars
        
        

class Py3dAutomask(AfniFunction):
    def __init__(self, prefix=None, clfrac=0.3, input=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.clfrac = clfrac
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'3dAutomask'}
        vars['-prefix'] = self.prefix
        vars['-clfrac'] = self.clfrac
        vars['$input'] = self.input
        return vars
        
        

class Py3dcalc(AfniFunction):
    def __init__(self, a=None, b=None, c=None, expr=None, prefix=None,
                 datum='float'):
        AfniFunction.__init__(self)
        self.a = a
        self.b = b
        self.c = c
        self.expr = expr
        self.prefix = prefix
        self.datum = datum
        
    @property
    def assignments(self):
        vars = {'$function':'3dcalc'}
        vars['-a'] = self.a
        vars['-b'] = self.b
        vars['-c'] = self.c
        vars['-expr'] = self.expr
        vars['-prefix'] = self.prefix
        vars['-datum'] = self.datum
        return vars
        
        

class Py3dTstat(AfniFunction):
    def __init__(self, prefix=None, input=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'3dTstat'}
        vars['-prefix'] = self.prefix
        vars['$input'] = self.input
        return vars
            
        
        
class Py3drefit(AfniFunction):
    def __init__(self, abuc=True, input=None):
        AfniFunction.__init__(self)
        self.abuc = abuc
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'3drefit'}
        if self.abuc:
            vars['-abuc'] = ''
        vars['$input'] = self.input
        return vars
            
        

class Py3dcopy(AfniFunction):
    def __init__(self, input=None, output=None):
        AfniFunction.__init__(self)
        self.input = input
        self.output = output
    
    @property
    def assignments(self):
        vars = {'$function':'3dcopy'}
        vars['$input'] = self.input
        vars['$output'] = self.output
        return vars
            
        

class Pyto3d(AfniFunction):
    def __init__(self, prefix=None, input=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'to3d'}
        vars['-prefix'] = self.prefix
        vars['$input'] = self.input
        return vars
            
        

class Py3dinfo(AfniFunction):
    def __init__(self, input=None):
        AfniFunction.__init__(self)
        self.input = input
        self.ioflag = True
        
    @property
    def assignments(self):
        vars = {'$function':'3dinfo'}
        vars['$input'] = self.input
        return vars
        
        
        
class Py3dTcat(AfniFunction):
    def __init__(self, prefix=None, input=None, leadin=None, leadout=None):
        AfniFunction.__init__(self)
        self.prefix = prefix
        self.input = input
        self.leadin = leadin
        self.leadout = leadout
        
    @property
    def assignments(self):
        vars = {'$function':'3dTcat'}
        vars['-prefix'] = self.prefix
        # no support yet for either individually:
        cut_input = self.input[:]
        if self.leadin and self.leadout:
            if isinstance(self.input,(list,tuple)):
                for i,input in enumerate(self.input):
                    cut_input[i] = input+'['+str(self.leadin)+'..'+str(self.leadout)+']'
            else:
                cut_input = self.input+'['+str(self.leadin)+'..'+str(self.leadout)+']'
            vars['$input'] = cut_input
        else:
            vars['$input'] = ' '.join(self.input)
        return vars
        
        
class Py3dTshift(AfniFunction):
    def __init__(self, slice=0, prefix=None, input=None):
        AfniFunction.__init__(self)
        self.slice = slice
        self.prefix = prefix
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'3dTshift'}
        vars['-slice'] = self.slice
        vars['-prefix'] = self.prefix
        vars['$input'] = self.input
        return vars
        

class PyAutoTalairach(AfniFunction):
    def __init__(self, warp_orig_vol=True, suffix='NONE', base=None, input=None):
        AfniFunction.__init__(self)
        self.warp_orig = warp_orig_vol
        self.suffix = suffix
        self.base = base
        self.input = input
        
    @property
    def assignments(self):
        vars = {'$function':'@auto_tlrc'}
        if self.warp_orig:
            vars['-warp_orig_vol'] = ''
        vars['-suffix'] = self.suffix
        vars['-base'] = self.base
        vars['-input'] = self.input
        return vars
        
        
class Pyadwarp(AfniFunction):
    def __init__(self, apar=None, dpar=None, dxyz=None):
        AfniFunction.__init__(self)
        self.apar = apar
        self.dpar = dpar
        self.dxyz = dxyz
        
    @property
    def assignments(self):
        vars = {'$function':'adwarp'}
        vars['-apar'] = self.apar
        vars['-dpar'] = self.dpar
        vars['-dxyz'] = self.dxyz
        return vars
        
        
        
            
                