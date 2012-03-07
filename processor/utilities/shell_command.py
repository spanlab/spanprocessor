#!/usr/bin/env python

import subprocess


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

def shell_command(cmdfull,ioflag=False,shell=False):
    if not shell and (type(cmdfull) == type('string')):
        cmd = cmdfull.split(' ')
    elif shell and type(cmdfull) == type([]):
        cmd = ' '.join(cmdfull)
    else:
        cmd = cmdfull
    if ioflag:
        afniproc = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=shell)
        afniproc.wait()
        output = afniproc.communicate()[0]
        return output
    else:
        afniproc = subprocess.call(cmd,shell=shell)
        return True
    
    
    
    

