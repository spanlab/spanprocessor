#!/usr/bin/env python

import os
import sys
import multiprocessing
import Queue
import subprocess
from pprint import pprint
import api


class Master:
    def __init__(self,threads,vars):
        self.threads = threads
        self.vars = vars
    
    def preprocess(self):
        inqueue = multiprocessing.Queue()
        outqueue = multiprocessing.Queue()
        for i,dir in enumerate(self.vars['subject_dirs']):
            inqueue.put([i,dir])
        completed = []
        for i in range(self.threads):
            PreProc = api.Preprocessor(data_type=self.vars['data_type'])
            PreProc.initialize_variables(self.vars)
            CurSlave = Slave(inqueue,outqueue,PreProc)
            CurSlave.start()
        
        while len(completed) < len(self.vars['subject_dirs']):
            num = outqueue.get()
            completed.append(num)
        return True
        
    

class Slave(multiprocessing.Process):
    def __init__(self,inqueue,outqueue,jobclass):
        multiprocessing.Process.__init__(self)
        self.inqueue = inqueue
        self.outqueue = outqueue
        self.jobclass = jobclass
        self.kill_recieved = False
    def run(self):
        while not self.kill_recieved:
            try:
                [num,jobdir] = self.inqueue.get_nowait()
            except Queue.Empty:
                break
            if jobdir:
                currentdir = os.getcwd()
                os.chdir(jobdir)
            self.jobclass.run()
            if jobdir:
                os.chdir(currentdir)
            self.outqueue.put(num)