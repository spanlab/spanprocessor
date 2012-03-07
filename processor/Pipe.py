#!/usr/bin/env python

import pkgutil
import glob
import copy
import inspect

from SorcerersApprentice import (SorcerersApprentice, Worker)

class Pipe(object):
    
    def __init__(self, variables):
        self.variables = variables
        self.process_chain = []
        self.job_list = []
        self._default_dset_name = 'functional'
        self.root_dir = self.find_root_dir()
        
    def _fill_in_variables(self, process):
        if not process.required_args_set:
            for argname in process.required_kwargs:
                if argname in self.variables:
                    process.set(argname=self.variables[argname])
        return process
        
    def add(self, *processes):
        for process in processes:
            process = self._fill_in_variables(process)
            self.process_chain.append(process)
            
    def find_root_dir(self):
        if hasattr(self,'variables'):
            if 'root_dir' in self.variables:
                return self.variables['root_dir']
            elif self.subjects:
                if glob.glob(self.subjects[0]+'*'):
                    return os.getcwd()
                elif glob.glob('../'+self.subjects[0]+'*'):
                    return os.path.split(os.getcwd())[0]
        else:
            if os.path.split(os.getcwd())[1] == 'scripts':
                return os.path.split(os.getcwd())[0]
            else:
                return os.getcwd()
        
    @property
    def subject_dirs(self):
        if hasattr(self,'variables') and ('subjects' in self.variables): 
            subjects = self.variables['subjects']
            root_dir = self.variables['root_dir']
            return [glob.glob(os.path.join(root_dir,sub)+'*')[0] for sub in subjects]
        else:
            return False
        
    @property
    def subjects(self):
        if hasattr(self,'variables') and ('subjects' in self.variables):
            return self.variables['subjects']
        else:
            return False
        
        
    def _wricursive(self,fid,depth,fraction):
        if isinstance(fraction,(list,tuple)):
            for fractal in fraction:
                self._wricursive(fid,depth+1,fractal)
        else:
            if fraction.startswith('#*'): #or fraction.startswith('cd'):
                fraction = fraction+'\n'
            tabs = '\t'*(depth)
            print depth
            print tabs+fraction
            fid.write(tabs+fraction+'\n')
            
            
    def _iterate_subjects(self,chain_write):
        if self.subjects:
            iterator = ['foreach subject ( '+' '.join(self.subjects)+ ' )\n\n']
            cder = ['cd ../${subject}*\n\n']
            cder.extend(chain_write)
            iterator.append(cder)
            iterator.append('end\n\n\n\n\n')
            return iterator
        else:
            return chain_write 
        
        
    def writeout(self,filename='tempfile'):
        
        self.chain_processes(writeout=True)
        master = []
        for process in self.process_chain:
            writeproc = process.writeout()
            #print writeproc
            writeproc.append('\n\n')
            master.extend(writeproc)
            #master.append(process.writeout())
        
        master = self._iterate_subjects(master)
        print master
        
        fileout = open('tempfile','w')
        self._wricursive(fileout,-1,master)
        fileout.close()
        
    def process_name_correction(self,processes):
        
        prior_dset = None
        
        for process in processes:
            
            if hasattr(process,'dset'):
                
                process.rectify_dset()
                
                suffix = getattr(process,'suffix_out',None) or ''   
                if not prior_dset:
                    if not getattr(process,'dset',None):
                        prior_dset = 'functional'+suffix
                    else:
                        prior_dset = process.dset+suffix
                    
                elif getattr(process,'dset',None):
                    if prior_dset.find(process.dset) != -1:
                        setattr(process,'dset',prior_dset)
                        prior_dset = prior_dset+suffix
                else:
                    setattr(process,'dset',prior_dset)
                    prior_dset = prior_dset+suffix
                        
            
            if hasattr(process,'process_directory'):
                process.rectify_paths()
                
            print prior_dset
                        
        return processes
    
    def chain_processes(self,writeout=False):
        self.process_name_correction(self.process_chain)
            
        
    def run(self):
        self.chain_processes(writeout=False)
        manager = SorcerersApprentice(threads=1,vars=self.vars)
        manager.addjobs(self.job_list)
        manager.spawn_workers()
        manager.start_workers()
        manager.wait_on_queue()
    
    
    
    
    
class SubjectPipe(Pipe):
    def __init__(self, variables):
        Pipe.__init__(variables)
        
    def chain_processes(self,writeout=False):
        
        if self.process_chain and self.subject_dirs:
            
            for dir in self.subject_dirs:
                
                process_copies = []
                for process in self.process_chain:
                    pcopy = copy.copy(process)
                    pcopy.process_directory = dir
                    process_copies.append(pcopy)
                
                new_processes = self.process_name_correction(process_copies)
                
                self.job_list.append(new_processes)
                    

    


            
    
    
        

        
        
    
    

            
            
            
            
            
            
            
            