#!/usr/bin/env python

import os
import glob
import string
import subprocess

'''
GENERAL_CLEANER
11.1.11     Kiefer Katovich

Cleans up the files you want erased. If headbrickflag is set to 1 or True,
it will clean up a file as if it were a prefix to an AFNI HEAD and BRIK
file pair. (also cleaning +tlrc)

Example 1:
    general_cleaner('anat',1)
    
This will clean anat+orig.HEAD, anat+orig.BRIK, anat+tlrc.HEAD, anat+tlrc.BRIK

Example 2:
general_cleaner('3dmotion.1D',0)

This cleans out the 3dmotion.1D file from the directory.

Simple!

'''

def general_cleaner(files,headbrikflag):

    if type(files) != type([]):
        files = [files]
    if headbrikflag:
        for file in files:
            if os.path.exists(file+'+orig.HEAD'): os.remove(file+'+orig.HEAD')
            if os.path.exists(file+'+orig.BRIK'): os.remove(file+'+orig.BRIK')
            if os.path.exists(file+'+tlrc.HEAD'): os.remove(file+'+tlrc.HEAD')
            if os.path.exists(file+'+tlrc.BRIK'): os.remove(file+'+tlrc.BRIK')
    else:
        for file in files:
            if os.path.exists(file): os.remove(file)
            
            

'''
PARSE_DIRS
11.01.11     Kiefer Katovich

Parse the folders in the current directories for only the ones you want.
Takes two keyworded arguments: prefixes and shave_front. prefixes defaults to an
empty list, and shave_front defaults to True. If you specify prefixes, it will
only return folders that begin with that prefix (ignoring the ./). If
shave_front is set to False, the ./ is included in the string filenames,
otherwise it is not.

Examples:

Lets say the directory is:
.
..
hey.txt
folder1/
folder2/
aa01/
bb02/

parsed = parse_dirs()
parsed = ['folder1/','folder2/','aa01/','bb02/']

parsed = parse_dirs(prefixes=['aa','bb'],shave_front=False)
parsed = ['./aa01/','./bb02/']

Could be better, but good enough fo' now.

'''

def parse_dirs(prefixes=[],exclude=[],shave_front=True):
    directory_contents = glob.glob('./*/')
    parsed = []
    if prefixes:
        for file in directory_contents:
            for prefix in prefixes:
                if (file.strip('./')).startswith(prefix):
                    if exclude:
                        flag = 0
                        for exclusion in exclude:
                            if (file.strip('./').startswith(exclusion)):
                                flag = 1
                        if not flag:
                            if shave_front:
                                parsed.append(file[2:])
                            else:
                                parsed.append(file)
                    else:
                        if shave_front:
                            parsed.append(file[2:])
                        else:
                            parsed.append(file)
    else:
        for file in directory_contents:
            if exclude:
                flag = 0
                for exclusion in exclude:
                    if (file.strip('./').startswith(exclusion)):
                        flag = 1
                if not flag:
                    if shave_front:
                        if len(file) > 2: parsed.append(file[2:])
                    else:
                        if len(file) > 2: parsed.append(file)
            else:
                if shave_front:
                    if len(file) > 2: parsed.append(file[2:])
                else:
                    if len(file) > 2: parsed.append(file)    
    return parsed



'''
SHELL_COMMAND
11.01.11     Kiefer Katovich

Takes a string command to be run through python's subprocess module. The string
entered will be split along spaces, as subprocess requires. Alternatively, a
list of commands can be entered already split along spaces. It is up to you!

The additional ioflag key'd argument specifies whether you want the output of
the function piped to stdout or not. The default is ioflag=0, which means that
subprocess.call() is used and no output is piped.

TECH NOTE: In this case subprocess' shell attribute is not set to true. If it
were, the command would not be split into a list. I feel that using shell=True
is not necessary.

Example 1:
shell_command('3dcopy randomdata.nii newdata')
OR shell_command(['3dcopy','randomdata.nii','newdata'])

This will call AFNI's 3dcopy command, converting randomdata.nii to AFNI's .HEAD
and .BRIK format.

Example 2:
output = shell_command('3dinfo newdata+orig',ioflag=1)

This will run AFNI's 3dinfo command on the newdata dataset. Since ioflag is set
to 1, the 3dinfo text will be piped into the output variable.

'''

def shell_command(cmdfull,ioflag=0):
    if type(cmdfull) == type('string'):
        cmd = cmdfull.split(' ')
    elif type(cmdfull) == type([]):
        cmd = cmdfull
    if ioflag:
        afniproc = subprocess.Popen(cmd,stdout=subprocess.PIPE)
        afniproc.wait()
        output = afniproc.communicate()[0]
        return output
    else:
        afniproc = subprocess.call(cmd)
        return True
