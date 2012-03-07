#!/usr/bin/env python


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

def general_cleaner(files,afni=False,writeout=False):
    
    whitebox = ['# Clean-up:']

    if type(files) != type([]):
        files = [files]
        
    whitebox.append('foreach file ( '+' '.join(files)+' ) ')
        
    if afni:
        if not writeout:
            for file in files:
                if os.path.exists(file+'+orig.HEAD'): os.remove(file+'+orig.HEAD')
                if os.path.exists(file+'+orig.BRIK'): os.remove(file+'+orig.BRIK')
                if os.path.exists(file+'+tlrc.HEAD'): os.remove(file+'+tlrc.HEAD')
                if os.path.exists(file+'+tlrc.BRIK'): os.remove(file+'+tlrc.BRIK')
            
        origcmd = ['if ( -e ${file}+orig.BRIK ) then', ['rm -rf ${file}+orig*'],
                   'endif']
        tlrccmd = ['if ( -e ${file}+tlrc.BRIK ) then', ['rm -rf ${file}+tlrc*'],
                   'endif']
        
        whitebox.append(origcmd)
        whitebox.append(tlrccmd)
            
    else:
        if not writeout:
            for file in files:
                if os.path.exists(file): os.remove(file)
            
        rmcmd = ['if ( -e ${file} ) then', ['rm -rf ${file}'], 'endif']
        whitebox.append(rmcmd)
        
    whitebox.append('end\n')
    
    if writeout:
        return whitebox
    else:
        return True
            
            
            
            
            
            
            
            