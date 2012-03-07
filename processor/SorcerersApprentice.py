#!/usr/bin/env python

import os
import sys
import threading
import Queue
import subprocess
from pprint import pprint


class SorcerersApprentice(object):
    def __init__(self,threads=1,vars=None):
        self.threads = threads
        self.vars = vars
        self.jobqueue = Queue.Queue()
        self.workers = []
        
    def addjobs(self,joblist):
        for job in joblist:
            self.jobqueue.put(job)
            
    def spawn_workers(self):
        for i in range(self.threads):
            worker = Worker(self.jobqueue,'worker_'+str(i))
            worker.setDaemon(True)
            self.workers.append(worker)
    
    def start_workers(self):
        for worker in self.workers:
            worker.start()
    
    def wait_on_queue(self):
        self.jobqueue.join()
        
    

class Worker(threading.Thread):
    def __init__(self,jobqueue,name):
        threading.Thread.__init__(self)
        self.queue = jobqueue
        self.name = name
        
        
        
    def parse_jobs(self,jobs):
        if isinstance(jobs,(list,tuple)):
            for job in jobs:
                self.parse_jobs(jobs)
            return True
        else:
            return self.process(jobs)
            
    
    def process(self,job):
        if not callable(getattr(job,'run')):
            pprint('Job passed to Worker without callable run function.\n')
            return False
        else:
            job.run()
            return True

    
    def run(self):
        while True:
            job = self.queue.get()
            attempt = self.parse_jobs(job)
            self.queue.task_done()






