#!/usr/bin/env python

# imports:
import os
import sys
import glob
import shutil
import inspect
from pprint import pprint
from mono_utility import (general_cleaner, shell_command)
import AfniFunctions


class Preprocessor(object):
    def __init__(self,var_dict):
        self.vars = var_dict
        self.function_order = []
        
    def add_function(self,function):
        add_flag = 1
        spec = inspect.getargspec(function)
        var_names = spec[0]
        def_values = spec[1:]
        set_values = []
        for name,value in zip(var_names,def_values):
            if name in self.vars:
                if self.vars[name]:
                    set_values.append(self.vars[name])
                elif value:
                    set_values.append(value)
                else:
                    print 'ERROR: Required function variable not in provided variables.\n'
                    add_flag = 0
            elif value:
                set_values.append(value)
            else:
                print 'ERROR: Required function variable not in provided variables.\n'
                add_flag = 0
        if add_flag:
            
    
        
        