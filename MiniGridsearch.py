#!/usr/bin/env python


import sys, os
import glob
import api
from pprint import pprint
import simplejson
import time
import math
import numpy as np



class MiniGridsearch(object):
    def __init__(self, vars, regobject, records_dir='./reg_output/records/',
                 seed=5., prefix='gs', suffix='', randomize=False, folds=5,
                 b1max=5.0, b2max=5.0, b3max=5.0, b4max=1000.):
        self.vars = vars
        self.seed = seed
        self.regreg = regobject
        self.records = records_dir
        self.topdir = os.getcwd()
        self.prefix = prefix
        self.suffix = suffix
        self.randomize = randomize
        self.folds = folds
        self.b1max = b1max
        self.b2max = b2max
        self.b3max = b3max
        self.b4max = b4max
        self.vars['crossvalidation_folds'] = self.folds
        
        
    def openjs(self,name):
        file = open(name,'r')
        return simplejson.load(file)
        
    
    def parsename(self,name):
        s = name.split('_')
        b1 = float(s[1])
        b2 = float(s[2])
        b3 = float(s[3])
        b4 = float(s[4].strip('.json'))
        return [b1,b2,b3,b4]
        
        
    def getacc(self,d):
        return float(d['mean_accuracy'])
        
        
    def getboundlimits(self,d):
        b1avelim = sum(d['l1_norms'])/len(d['l1_norms'])
        b2avelim = sum(d['l2_norms'])/len(d['l2_norms'])
        b3avelim = sum(d['graphnet_norms'])/len(d['graphnet_norms'])
        return [b1avelim,b2avelim,b3avelim]
        
    
    def values(self,name):
        d = self.openjs(name)
        bvals = self.parsename(name)
        name_vals = [name]
        name_vals.extend(bvals)
        name_vals.append(self.getacc(d))
        return name_vals
    
    
    def sortbyacc(self,tests,ind):
        return sorted(tests, key=lambda list: list[ind])
    
    
    def getmaxname(self,sort):
        maxval = 0
        maxname = ''
        for item in sort:
            if item[5] > maxval:
                maxval = item[5]
                maxname = item[0]
        return maxname
    
    
    def gettop(self,sort,number):
        maxvals = []
        maxnames = []
        for item in sort[-number:]:
            maxvals.append(item[5])
            maxnames.append(item[0])
        return maxnames
        
    
        
    def get_file(self,b1,b2,b3,b4):
        filename = self.prefix+'_'+str(b1)+'_'+str(b2)+'_'+str(b3)+'_'+str(b4)+'_'+self.suffix+'.json'
        if os.path.exists(os.path.join(self.records,filename)):
            return self.openjs(os.path.join(self.records,filename))
        else:
            return False
    
    def set_filename(self,b1,b2,b3,b4):
        filename = self.prefix+'_'+str(b1)+'_'+str(b2)+'_'+str(b3)+'_'+str(b4)+'_'+self.suffix
        self.vars['output_filename'] = filename
        
        
    def bound_splitter(self,split_depth,bound,b1,b2,b3,b4,style='fractal'):
        if split_depth > 0:
            b1_1 = min(b1,self.b1max)
            b1_2 = min(b1,self.b1max)
            b2_1 = min(b2,self.b2max)
            b2_2 = min(b2,self.b2max)
            b3_1 = min(b3,self.b3max)
            b3_2 = min(b3,self.b3max)
            b4_1 = min(b4,self.b4max)
            b4_2 = min(b4,self.b4max)
            b4_3 = min(b4,self.b4max)
            b4_4 = min(b4,self.b4max)
            
            if bound == 1:
                if style == 'fractal':
                    b1_1 = min(b1-(b1/2),self.b1max)
                    b1_2 = min(b1+(b1/2),self.b1max)
                
            elif bound == 2:
                if style == 'fractal':
                    b2_1 = min(b2-(b2/2),self.b2max)
                    b2_2 = min(b2+(b2/2),self.b2max)
                
            elif bound == 3:
                if style == 'fractal':
                    b3_1 = min(b3-(b3/2),self.b3max)
                    b3_2 = min(b3+(b3/2),self.b3max)
                
            elif bound == 4:
                b4_1 = min(1.,self.b4max)
                b4_2 = min(10.,self.b4max)
                b4_3 = min(100.,self.b4max)
                b4_4 = min(1000.,self.b4max)
                    
                
            if not bound == 4:
                self.initialize_bounds(b1_1,b2_1,b3_1,b4_1)
                self.runreg()
                self.initialize_bounds(b1_2,b2_2,b3_2,b4_2)
                self.runreg()
                self.bound_splitter(split_depth-1,bound,b1_1,b2_1,b3_1,b4_1)
                self.bound_splitter(split_depth-1,bound,b1_2,b2_2,b3_2,b4_2)
            else:
                self.initialize_bounds(b1_1,b2_1,b3_1,b4_1)
                self.runreg()
                self.initialize_bounds(b1_1,b2_1,b3_1,b4_2)
                self.runreg()
                self.initialize_bounds(b1_1,b2_1,b3_1,b4_3)
                self.runreg()
                self.initialize_bounds(b1_1,b2_1,b3_1,b4_4)
                self.runreg()
            
            return True
        else:
            return True
        
        
    def general_pass(self,b2mult,b3mult,b4=0):
        b1_net = [self.seed*m for m in [0.01, 0.05, 0.1, 0.3, 0.5, 1., 1.5, 2., 2.5, 3.5]]
        bound_sets = []
        for b1 in b1_net:
            bound_sets.append([b1,b1*b2mult,b1*b3mult,b4])
        for bset in bound_sets:
            self.initialize_bounds(bset[0],bset[1],bset[2],bset[3])
            self.runreg()
        return bound_sets
    
    
    def linear_search(self, b1r, b2r, b3r, b4r):
        for b2 in b2r:
            for b3 in b3r:
                for b4 in b4r:
                    for b1 in b1r:
                        print b1, b2, b3, b4
                        self.initialize_bounds(b1,b2,b3,b4)
                        self.runreg()
                        
    
    
    '''
    def find_bound_multiples(self,bound_sets):
        
        b1lims = []
        b2lims = []
        b3lims = []
        
        for bset in bound_sets:
            fid = self.get_file(bset[0],bset[1],bset[2])
            if fid:
                [b1L,b2L,b3L] = self.getboundlimits(fid)
                b1lims.append(b1L)
                b2lims.append(b2L)
                b3lims.append(b3L)
                
        b2fracs = []
        b3fracs = []
        for i,b1 in enumerate(b1lims):
            b2fracs.append(b2lims[i]/b1)
            b3fracs.append(b3lims[i]/b1)
            
        fid.close()
            
        print b2fracs
        print b3fracs
        
        return [sum(b2fracs)/len(b2fracs), sum(b3fracs)/len(b3fracs)]
    '''
    
            
    def initial_pass(self):
        sets = self.general_pass(1.,1.)
        return sets
    
    '''        
    def bound_explorer(self,sets):
        [b2mult,b3mult] = self.find_bound_multiples(sets)
        for m in [0.5, 0.25, 0.1, 0.01]:
            nsets = self.general_pass(b2mult*m, b3mult*m)
    '''        
    
    def searchtop(self,ranklength):
        os.chdir(self.records)        
        jsons = glob.glob('*.json')
        bvals = []
        for name in jsons:
            bvals.append(self.values(name))
        bvals = self.sortbyacc(bvals,5)
        
        topten = self.gettop(bvals,ranklength)
        print topten
        os.chdir(self.topdir)
        return topten
    
    
    def hone_topranked(self, depth, ranklength, bounds=[1,2,3,4]):
        topten = self.searchtop(ranklength)
        last_try = 0
        stop = 0
        while not stop:
            for bound in bounds:
                for record in topten:
                    [cb1,cb2,cb3,cb4] = self.parsename(record)
                    self.bound_splitter(depth,bound,cb1,cb2,cb3,cb4)
            next_topten = self.searchtop(ranklength)
            if next_topten == topten:
                stop = 1
                break
            else:
                topten = next_topten
        return True
    
        
    def set_maxes(self):
        #b1 = 100
        #b2 = 100
        #b3 = 100
        #b4 = 0
        #self.initialize_bounds(b1,b2,b3,b4)
        #self.runreg()
        #maxfile = self.get_file(b1,b2,b3,b4)
        #[limb1,limb2,limb3] = self.getboundlimits(maxfile)
        self.b1max = 30.
        self.b2max = 10.
        self.b3max = 10.
        print self.b1max
        time.sleep(3.0)
        
        
    def initialize_bounds(self,b1,b2,b3,b4):
        self.vars['random_seed'] = np.random.randint(0,1000000000)
        self.vars['bound1'] = b1
        self.vars['bound2'] = b2
        self.vars['bound3'] = b3
        self.vars['lambda3'] = b4
        self.set_filename(b1,b2,b3,b4)
        
        
        
    def runreg(self):
        if self.get_file(self.vars['bound1'],self.vars['bound2'],self.vars['bound3'],
                         self.vars['lambda3']):
            pass
        else:
            self.regreg.initialize_variables(self.vars)
            self.regreg.run()
            
            
    def run(self):
        self.set_maxes()
        
        b1range = range(1,31)
        b2range = [0.1, 0.5, 1, 5]
        b3range = [0.1, 0.5, 1, 5]
        b4range = [0., 1, 100, 1000]
        
        self.linear_search(b1range, b2range, b3range, b4range)
        
        
        '''
        sets = self.initial_pass()
        self.hone_topranked(1,10,bounds=[1])
        self.hone_topranked(1,10,bounds=[2])
        self.hone_topranked(1,10,bounds=[3])
        self.hone_topranked(1,10,bounds=[4])
        '''
        
        
        
        
        
        
        
        
        
        
        
        