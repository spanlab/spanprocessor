#!/usr/bin/env python

import os
import sys
import threading
import Queue
import subprocess
from pprint import pprint
import api


class Manager:
    def __init__(self,threads,vars):
        self.threads = threads
        self.vars = vars
        self.jobqueue = Queue.Queue()
        self.workers = []
        
    def add_jobs(self,*args):
        for jobclass in args:
            if type(jobclass) == type([]):
                self.add_jobs(jobclass)
            elif callable(getattr(jobclass,'run')):
                self.jobqueue.put(jobclass)
            else:
                pprint('Invalid job: neither list of jobs nor job class with run() function.\n')
            
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
        
    def run(self):
        while True:
            jobclass = self.queue.get()
            if not callable(getattr(jobclass,'run')):
                pprint('Job passed to Worker without callable run function.\n')
                break
            else:
                jobclass.run()
            self.queue.task_done()
