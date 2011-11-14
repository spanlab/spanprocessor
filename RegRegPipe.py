#!/usr/bin/env python

from pprint import pprint
import subprocess
import sys, os
import numpy as np
import scipy as sp
from scipy import sparse
from scipy import io
import nibabel as nib
import regreg.api as rr
import regreg.mask as mask
from mono_utility import (general_cleaner, shell_command)


class RegRegPipe:
    def __init__(self):
        self.required_vars = ['reg_nifti_name','reg_mask_name','reg_resp_vec_name',\
                              'reg_onset_vec_name','reg_response_tr','reg_subjects',\
                              'reg_total_trials','reg_prediction_tr_len','reg_mask_dir',\
                              'lag','reg_experiment_trs','reg_trial_trs','scripts_dir',\
                              'dynamic_iti','lambda1','bound1','lambda2','lambda3','bound3',\
                              'inv_step','set_tol','max_its','lookback','lookback_trs']
        self.variables_initialized = False
        self.loaded_nifti_data = False
        self.parsed_response_vectors = False
        self.created_reg_mask = False
        self.combined_data_vectors = False
        self.normalized = False
        self.ridge_defined = False
        self.graphnet_defined = False
        self.loss_defined = False
        self.sparsity_defined = False
        self.sparse_matrix_defined = False
        self.problem_defined = False
        self.problem_solved = False
        self.output_complete = False
        
    
    def initialize_variables(self,var_dict):
        self.lookback = False
        self.lookback_trs = 0
        self.var_dict = var_dict
        for key, value in var_dict.items():
            setattr(self,key,value)
        for var_name in self.required_vars:
            if not var_name in var_dict:
                print 'WARNING: %s was NOT included in the variable dictionary!\n' % var_name
                print 'Not including %s may or may not break the pipeline.\n' % var_name
                print 'Know what you are doing!\n'
                setattr(self,var_name,False) 
        self.design = []
        self.Y = []
        self.variables_initialized = True
    
    def __load_nifti(self,nifti):
        image = nib.load(nifti)
        idata = image.get_data()
        affine = image.get_affine()
        return [idata,affine]
        
    def load_nifti_data(self):
        setattr(self,'raw_data_list',[])
        setattr(self,'raw_affine',[])
        for subject in self.reg_subjects:
            os.chdir(subject)
            print os.getcwd()
            [idata,affine] = self.__load_nifti(self.reg_nifti_name)
            if self.reg_experiment_trs == False:
                self.reg_experiment_trs = len(idata[3])
            if self.reg_total_trials == False:
                if self.reg_trial_trs:
                    self.reg_total_trials = self.reg_experiment_trs/self.reg_trial_trs
            self.raw_data_list.append(np.array(idata))
            if self.raw_affine == []:
                self.raw_affine = affine
            os.chdir('../')
        self.loaded_nifti_data = True
        
    def __parse_vector(self,vector):
        vfile = open(vector,'rb')
        vlines = vfile.readlines()
        varray = np.zeros(shape=(len(vlines),1))
        for i in range(len(vlines)):
            vline = int(vlines[i].strip('\n'))
            if vline == 1 or vline == -1:
                varray[i] = vline
        return varray
        
    def parse_resp_vecs(self):
        setattr(self,'resp_vecs',[])
        setattr(self,'onset_vecs',[])
        for subject in self.reg_subjects:
            os.chdir(subject)
            print os.getcwd()
            resp_array = self.__parse_vector(self.reg_resp_vec_name)
            self.resp_vecs.append(resp_array)
            if self.dynamic_iti:
                onset_vec = self.__parse_vector(self.reg_onset_vec_name)
                self.onset_vecs.append(onset_vec)
            os.chdir('../')
        self.parsed_response_vectors = True
    
    def create_reg_mask(self):
        currentdir = os.getcwd()
        if self.reg_mask_dir: os.chdir(self.reg_mask_dir)
        [self.mask_data,self.mask_affine] = self.__load_nifti(self.reg_mask_name)
        self.m = np.zeros([self.mask_data.shape[0],self.mask_data.shape[1],\
                           self.mask_data.shape[2],self.reg_prediction_tr_len],np.bool)
        for i in range(self.reg_prediction_tr_len):
            self.m[:,:,:,i] = self.mask_data[:,:,:]
        self.p = np.sum(self.m)
        if self.reg_mask_dir: os.chdir(currentdir)
        self.created_reg_mask = True
        
    def combine_data_vectors(self):
        # Take all the functional data and the response vectors and concatenate
        # them into the self.design and self.Y lists, respectively
        #
        # go through all trials-1 and grab the "trial" amount of TRs.
        # put that trial into a temp variable and then append the trial
        # to self.design (but use self.m to mask out extraneous voxels)
        #
        # take the response vector of 1s and 0s, and take out the indices for
        # the "response tr" (likely the TR where they are making a choice).
        # this list comprehension is pretty nasty, but basically it goes through
        # the number of trials-1, multiplies that trial by the TR that the
        # response lands on to get the index of the response TR.
        # Yikes.
        if not self.dynamic_iti:
            for (data,respvec) in zip(self.raw_data_list,self.resp_vecs):
                for i in range(self.reg_total_trials-1):  
                    trial = data[:,:,:,(self.lag+i*self.reg_trial_trs):(self.lag+(i+1)*self.reg_trial_trs)]
                    self.design.append(trial[self.m])
                self.Y.extend(respvec[[(y+1)*(self.reg_response_tr-1) for y in range(self.reg_total_trials-1)]])
        elif self.dynamic_iti:
            for (data,respvec,onsetvec) in zip(self.raw_data_list,self.resp_vecs,self.onset_vecs):
                onsetindices = np.nonzero(onsetvec)[0]
                if not self.lookback:
                    for ind in onsetindices:
                        trial = data[:,:,:,(ind+self.lag):(ind+self.reg_trial_trs+self.lag)]
                        self.design.append(trial[self.m])
                        # response vector here should have every TR in trial marked with response!
                        self.Y.extend(respvec[ind])
                elif self.lookback:
                    for ind in onsetindices:
                        if not ind == 0:
                            trial = data[:,:,:,(ind+self.lag-self.lookback_trs):(ind+self.reg_trial_trs+self.lag)]
                            self.design.append(trial[self.m])
                            # response vector here should have every TR in trial marked with response!
                            self.Y.extend(respvec[ind])
        self.combined_data_vectors = True
    
    def normalize(self):
        self.design = np.array(self.design)
        self.X_nonnorm = np.vstack(self.design)
        #temp = np.std(self.X_nonnorm,axis=0)
        #for x in temp:
        #    pprint(x)
        #self.X = (self.X_nonnorm - np.mean(self.X_nonnorm,axis=0))/np.std(self.X_nonnorm,axis=0)
        self.X = self.X_nonnorm
        #self.X = rr.normalize(self.X_nonnorm,center=True,scale=True)
        pprint(self.X)
        self.normalized = True
    
    def define_loss(self,set_coef=0.5):
        self.Y = np.array(self.Y)
        self.loss = rr.quadratic.affine(self.X,-self.Y,coef=set_coef)
        #self.loss = rr.l2norm.affine(self.X,-self.Y,lagrange=set_lagrange)
        self.loss_defined = True
        
    def define_ridge(self,set_coef=None):
        if set_coef is None:
            set_coef = self.lambda2
        self.ridge = rr.quadratic(self.p,coef=set_coef)
        #self.ridge = rr.l2norm(self.p,lagrange=set_lagrange)
        self.ridge_defined = True
    
    def define_sparsity(self,set_lagrange=None,set_bound=None):
        if set_lagrange is None:
            set_lagrange = self.lambda1
        if set_bound is None:
            set_bound = self.bound1
        self.sparsity = rr.l1norm(self.p,lagrange=set_lagrange)
        self.sparsity_bound = rr.l1norm(self.p,bound=set_bound)
        self.sparsity_defined = True

    def define_sparse_matrix(self,search_mat=True):
        if search_mat:
            if os.path.exists('sparsematrix.mat'):
                self.D = io.loadmat('sparsematrix.mat')['D']
            else:
                self.adj = mask.prepare_adj(self.m,numx=1,numy=1,numz=1,numt=1)
                self.D = sparse.csr_matrix(mask.create_D(self.adj))
                pprint(self.D)
                io.savemat('sparsematrix',{'D':self.D})
        else:
            general_cleaner('sparsematrix.mat')
            self.adj = mask.prepare_adj(self.m,numx=1,numy=1,numz=1,numt=1)
            self.D = sparse.csr_matrix(mask.create_D(self.adj))
            pprint(self.D)
            io.savemat('sparsematrix',{'D':self.D})
        self.sparse_matrix_defined = True
    
    def define_graphnet(self,set_coef=None,set_bound=None,set_epsilon=0.01):
        if set_coef is None:
            set_coef = self.lambda3
        if set_bound is None:
            set_bound = self.bound3
        self.graphnet = rr.quadratic.linear(self.D,coef=set_coef)
        #self.graphnet = rr.l2norm.linear(self.D,lagrange=set_lagrange)
        self.graphnet_bound = rr.l2norm.linear(self.D,bound=set_bound)
        self.graphnet_bound_smooth = rr.smoothed_atom(self.graphnet_bound, epsilon=set_epsilon)
        self.glasso_bound = rr.l1norm.linear(self.D,bound=set_bound)
        self.glasso_bound_smooth = rr.smoothed_atom(self.graphnet_bound, epsilon=set_epsilon)
        self.graphnet_defined = True
        
    def define_problem(self,loss=None,ridge=None,sparsity=None,graphnet=None,
                       coef_multiplier=0.0001):
        if loss is None:
            loss = self.loss
        if ridge is None:
            ridge = self.ridge
        if sparsity is None:
            sparsity = self.sparsity_bound
            #sparsity = self.sparsity
        if graphnet is None:
            graphnet = self.glasso_bound_smooth
            #graphnet = self.graphnet
        #set up the problem object:
        self.problem = rr.container(loss,ridge,sparsity,graphnet)
        self.problem.coefs = np.random.standard_normal(self.problem.coefs.shape) * 0.0001
        #set up the problem solver (FISTA):
        self.solver = rr.FISTA(self.problem)
        #set up problem debug as true:
        self.solver.debug = True
        self.problem_defined = True

    def solve_problem(self):
        #solve the problem:
        self.solver.fit(tol=self.set_tol,start_inv_step=self.inv_step,max_its=self.max_its)
        #grab the coefficients:
        self.solution = self.solver.composite.coefs
        #reshape the data!!
        self.solution_shaped = np.zeros((self.mask_data.shape[0],self.mask_data.shape[1], \
                                         self.mask_data.shape[2],self.reg_prediction_tr_len))
        self.solution_shaped[np.where(self.m)] = self.solution
        self.problem_solved = True
    
    def output_nii(self):
        output_filename = 'rr_%(n)sn_r%(ridge)1.1e_s%(sparsity)1.1e_g%(graph)1.1e' % \
                          {'n':len(self.reg_subjects),'ridge':self.lambda2,'sparsity':self.lambda1,\
                           'graph':self.lambda3}
        newnii = nib.Nifti1Image(self.solution_shaped,self.mask_affine)
        general_cleaner(output_filename+'.nii',0)
        general_cleaner(output_filename,1)
        newnii.to_filename(output_filename+'.nii')
        #shell_command(['3dcopy',output_filename+'nii',output_filename])
        self.output_complete = True
    
    def run(self):
        if self.variables_initialized:
            self.load_nifti_data()
            self.parse_resp_vecs()
            self.create_reg_mask()
            self.combine_data_vectors()
            self.normalize()
            self.define_loss()
            self.define_ridge()
            self.define_sparsity()
            self.define_sparse_matrix()
            self.define_graphnet()
            self.define_problem()
            self.solve_problem()
            self.output_nii()
        else:
            print '\nERROR: Impossible to run() without initializing variables.\n'
        

    
    
    
    
    
    
    
    
    
    
    
    