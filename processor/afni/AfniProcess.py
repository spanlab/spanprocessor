#!/usr/bin/env python

import inspect
from functools import wraps

from ..utilities import (general_cleaner, parse_dirs, shell_command)

class AfniProcess(object):
    def __init__(self):
        self.whitebox = None
        self.process_directory = None
        self.experiment_topdir = None
        self.super_attributes = self._get_user_variables()
    
    
    def _whitebox_extend(self,*args):
        for arg in args:
            self.whitebox.extend(arg)
    

    @property
    def required_args_set(self):
        for argument in self.required_kwargs:
            if getattr(self,argument,None):
                pass
            else:
                print 'WARNING:'
                print(argument+' in '+self.__class__.__name__+' is not set, or set to None.\n')
                #return False
        return True

    
    def set(self,**kwargs):
        for argument,value in kwargs.items():
            if not argument in self.required_kwargs():
                print(argument+' is not required for '+self.__class__.__name__+', but set regardless.\n')
            setattr(self,argument,value)
        return True
 
    def write_bash(self,filename):
        pass
            
    def commands(self,writeout=False):
        pass
    
    @property
    def required_kwargs(self):
        argnames,varargs,kwargs,defaults = inspect.getargspec(self.__init__)
        return [args for args in argnames if args not in ['self']]
       
    
    def _get_user_variables(self):
        generic_attributes = dir(type('dummy',(object,), {}))
        class_attributes = dir(self)
        variable_list = []
        for attr in class_attributes:
            if generic_attributes.count(attr) or callable(getattr(self,attr)):
                continue
            variable_list += [attr]
        if hasattr(self,'super_attributes'):
           variable_list = [attr for attr in variable_list if not attr in self.super_attributes]
        else:
            variable_list += ['super_attributes']
        return variable_list
    
    
    def rectify_dset(self):
        if hasattr(self,'dset') and getattr(self,'dset',None):
            format = None
            dset = None
            if self.dset.find('+orig') is not -1:
                dset = self.dset[:self.dset.find('+orig')]
                format = '+orig'
            elif self.dset.find('+tlrc') is not -1:
                dset = self.dset[:self.dset.find('+tlrc')]
                format = '+tlrc'
            if dset:
                print dset
                setattr(self,'dset',dset)
                print self.dset
            if format:
                setattr(self,'format',format)
                
                
    def rectify_paths(self):
        
        if self.process_directory:
            for attr in ('dset','motion_label','anat_name','raw_anat','raw_funcs'):
                if hasattr(self,attr):
                    cur_attr = getattr(self,attr,None)
                    if cur_attr:
                        if isinstance(cur_attr,(list,tuple)):
                            setattr(self,attr,[os.path.join(self.process_directory,x) for x in cur_attr])
                        else:
                            setattr(self,attr,os.path.join(self.process_directory,cur_attr))            
            return True
        else:
            return False
    

    def output(self):
        return {key:getattr(self,key) for key in self._get_user_variables()}
    
    
    def writeout(self):
        if self.required_args_set:
            self.commands(writeout=True)
            return self.whitebox
        
    
    def run(self,writeout=False):
        if self.required_args_set:
            self.commands()
            return True
            


        
        
