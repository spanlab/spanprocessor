#!/usr/bin/env python


import sys, os
import glob
import api
from pprint import pprint
import simplejson
import time



class MiniGridsearch(object):
    def __init__(self, vars, regobject, records_dir='./reg_output/records/',
                 seed=1., prefix='gs', suffix='', randomize=False, folds=5):
        self.vars = vars
        self.seed = seed
        self.regreg = regobject
        self.records = records_dir
        self.topdir = os.getcwd()
        self.prefix = prefix
        self.suffix = suffix
        self.randomize = randomize
        self.folds = folds
        self.vars['crossvalidation_folds'] = self.folds
        
        
    def openjs(self,name):
        file = open(name,'r')
        return simplejson.load(file)
        
    
    def parsename(self,name):
        s = name.split('_')
        b1 = float(s[1])
        b2 = float(s[2])
        b3 = float(s[3].strip('.json'))
        return [b1,b2,b3]
        
        
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
            if item[4] > maxval:
                maxval = item[4]
                maxname = item[0]
        return maxname
    
    def gettop(self,sort,number):
        maxvals = []
        maxnames = []
        for item in sort[-number:]:
            maxvals.append(item[4])
            maxnames.append(item[0])
        return maxnames
        
    
        
    def get_file(self,b1,b2,b3):
        filename = self.prefix+'_'+str(b1)+'_'+str(b2)+'_'+str(b3)+'_'+self.suffix+'.json'
        if os.path.exists(os.path.join(self.records,filename)):
            return self.openjs(os.path.join(self.records,filename))
        else:
            return False
    
    def set_filename(self,b1,b2,b3):
        filename = self.prefix+'_'+str(b1)+'_'+str(b2)+'_'+str(b3)+'_'+self.suffix
        self.vars['output_filename'] = filename
        
        
    def bound_splitter(self,split_depth,bound,b1,b2,b3):
        if split_depth > 0:
            if bound == 1:
                self.initialize_bounds(b1-(b1/2),b2,b3)
                self.runreg()
                self.initialize_bounds(b1+(b1/2),b2,b3)
                self.runreg()
                self.bound_splitter(split_depth-1,bound,b1-(b1/2),b2,b3)
                self.bound_splitter(split_depth-1,bound,b1+(b1/2),b2,b3)
            elif bound == 2:
                self.initialize_bounds(b1,b2-(b2/2),b3)
                self.runreg()
                self.initialize_bounds(b1,b2+(b2/2),b3)
                self.runreg()
                self.bound_splitter(split_depth-1,bound,b1,b2-(b2/2),b3)
                self.bound_splitter(split_depth-1,bound,b1,b2+(b2/2),b3)
            elif bound == 3:
                self.initialize_bounds(b1,b2,b3-(b3/2))
                self.runreg()
                self.initialize_bounds(b1,b2,b3+(b3/2))
                self.runreg()
                self.bound_splitter(split_depth-1,bound,b1,b2,b3-(b3/2))
                self.bound_splitter(split_depth-1,bound,b1,b2,b3+(b3/2))
            return True
        else:
            return True
        
    def general_pass(self,b2mult,b3mult):
        b1_net = [self.seed*m for m in [0.01, 0.05, 0.1, 0.5, 1., 1.5, 2., 10.]]
        bound_sets = []
        for b1 in b1_net:
            bound_sets.append([b1,b1*b2mult,b1*b3mult])
        for set in bound_sets:
            self.initialize_bounds(set[0],set[1],set[2])
            self.runreg()
        return bound_sets
    
    def find_bound_multiples(self,bound_sets):
        
        b1lims = []
        b2lims = []
        b3lims = []
        
        for set in bound_sets:
            file = self.get_file(set[0],set[1],set[2])
            if file:
                [b1L,b2L,b3L] = self.getboundlimits(file)
                b1lims.append(b1L)
                b2lims.append(b2L)
                b3lims.append(b3L)
                
        b2fracs = []
        b3fracs = []
        for i,b1 in enumerate(b1lims):
            b2fracs.append(b2lims[i]/b1)
            b3fracs.append(b3lims[i]/b1)
            
        print b2fracs
        print b3fracs
        
        return [sum(b2fracs)/len(b2fracs), sum(b3fracs)/len(b3fracs)]
            
            
    def initial_pass(self):
        sets = self.general_pass(1.,1.)
        return sets
            
    def bound_explorer(self,sets):
        [b2mult,b3mult] = self.find_bound_multiples(sets)
        for m in [0.5, 0.25, 0.1, 0.01]:
            nsets = self.general_pass(b2mult*m, b3mult*m)
    
    def searchtop(self,ranklength):
        os.chdir(self.records)        
        jsons = glob.glob('*.json')
        bvals = []
        for name in jsons:
            bvals.append(self.values(name))
        bvals = self.sortbyacc(bvals,4)
        
        topten = self.gettop(bvals,ranklength)
        print topten
        os.chdir(self.topdir)
        return topten
    
    
    def hone_topranked(self,depth,ranklength):
        topten = self.searchtop(ranklength)
        stop = 0
        while not stop:
            for bound in [1,2,3]:
                for record in topten:
                    [cb1,cb2,cb3] = self.parsename(record)
                    self.bound_splitter(depth,bound,cb1,cb2,cb3)
            next_topten = self.searchtop(ranklength)
            if next_topten == topten:
                stop = 1
                break
            else:
                topten = next_topten
        return True
        
        
    def initialize_bounds(self,b1,b2,b3):
        self.vars['bound1'] = b1
        self.vars['bound2'] = b2
        self.vars['bound3'] = b3
        self.set_filename(b1,b2,b3)
        
        
        
    def runreg(self):
        if self.get_file(self.vars['bound1'],self.vars['bound2'],self.vars['bound3']):
            pass
        else:
            self.regreg.initialize_variables(self.vars)
            self.regreg.run()
            
            
    def run(self):
        sets = self.initial_pass()
        #self.bound_explorer(sets)
        self.hone_topranked(2,8)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        