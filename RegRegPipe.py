
#!/usr/bin/env python

from pprint import pprint
import subprocess
import sys, os
import random
import numpy as np
import scipy as sp
from scipy import sparse
from scipy import io
import nibabel as nib
import regreg.api as rr
from regreg.affine import selector
import regreg.mask as mask
from mono_utility import (general_cleaner, shell_command)


class RegRegPipe:
    def __init__(self):
        self.required_vars = ['reg_nifti_name','reg_mask_name','reg_resp_vec_name',\
                              'reg_onset_vec_name','reg_response_tr','reg_subjects',\
                              'reg_total_trials','reg_prediction_tr_len','reg_mask_dir',\
                              'lag','reg_experiment_trs','reg_trial_trs','scripts_dir',\
                              'dynamic_iti','lambda1','bound1','lambda2','lambda3','bound3',\
                              'inv_step','set_tol','max_its','lookback','lookback_trs',\
                              'use_mask']
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
        
        self.vecfile1 = open('vec1output.txt','w')
        self.vecfile2 = open('vec2output.txt','w')
        

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
        shape = image.get_shape()
        idata = image.get_data()
        affine = image.get_affine()
        return [idata,affine,shape]
        
    def load_nifti_data(self):
        setattr(self,'raw_data_shape',[])
        setattr(self,'raw_data_list',[])
        setattr(self,'raw_affine',[])
        if type(self.reg_nifti_name) != type ([]):
            self.reg_nifti_name = [self.reg_nifti_name]
        for subject in self.reg_subjects:
            os.chdir(subject)
            print os.getcwd()
            for nifti_name in self.reg_nifti_name:
                pprint(nifti_name)
                if os.path.exists(nifti_name):
                    [idata,affine,ishape] = self.__load_nifti(nifti_name)
                    pprint(ishape)
                    if self.reg_experiment_trs == False:
                        self.reg_experiment_trs = len(idata[3])
                    if self.reg_total_trials == False:
                        if self.reg_trial_trs:
                            self.reg_total_trials = self.reg_experiment_trs/self.reg_trial_trs
                    self.raw_data_list.append(np.array(idata))
                    if self.raw_affine == []:
                        self.raw_affine = affine
                    if self.raw_data_shape == []:
                        self.raw_data_shape = ishape
                        pprint(ishape)
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
        if type(self.reg_resp_vec_name) != type([]):
            self.reg_resp_vec_name = [self.reg_resp_vec_name]
        for subject in self.reg_subjects:
            os.chdir(subject)
            print os.getcwd()
            for resp_vec in self.reg_resp_vec_name:
                if os.path.exists(resp_vec):
                    resp_array = self.__parse_vector(resp_vec)
                    self.resp_vecs.append(resp_array)
            if self.dynamic_iti:
                onset_vec = self.__parse_vector(self.reg_onset_vec_name)
                self.onset_vecs.append(onset_vec)
            os.chdir('../')
        self.parsed_response_vectors = True
    
    def create_reg_mask(self):
        currentdir = os.getcwd()
        if self.reg_mask_dir: os.chdir(self.reg_mask_dir)
        [self.mask_data,self.mask_affine,self.mask_shape] = self.__load_nifti(self.reg_mask_name)
        self.m = np.zeros([self.mask_shape[0],self.mask_shape[1],\
                           self.mask_shape[2],self.reg_prediction_tr_len],np.bool)
        for i in range(self.reg_prediction_tr_len):
            self.m[:,:,:,i] = self.mask_data[:,:,:]
        #self.p = np.sum(self.m)
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
        
        # Non-dynamic iti function is a bit obsolete. Probably works but needs
        # updating:
        
        
        
        if not self.dynamic_iti:
            difference = self.reg_trial_trs-self.reg_prediction_tr_len
            respdiff = self.reg_trial_trs-self.reg_response_tr
            
            for (data,respvec) in zip(self.raw_data_list,self.resp_vecs):
                
                temp_trials = []
                positive_trial_ind = []
                negative_trial_ind = []
                min_limit = 0

                
                for i in range(self.reg_total_trials-1):
                    # without downsampling:
                    #trial = data[:,:,:,(self.lag+i*self.reg_trial_trs):(self.lag+(i+1)*self.reg_trial_trs-difference)]
                    #self.design.append(trial[self.m])
                    
                    # with downsampling:
                    temp_trials.append(data[:,:,:,(self.lag+i*self.reg_trial_trs):(self.lag+(i+1)*self.reg_trial_trs-difference)])
                    
                    #print(len(self.design))
                
                # calculate the response vector:
                parsed_resp_vec = respvec[[((y+1)*(self.reg_trial_trs))-respdiff-1 for y in range(self.reg_total_trials-1)]]
                
                # without downsampling:
                #self.Y.extend(parsed_resp_vec)
                
                # downsampling response categorization:
                for i,response in enumerate(parsed_resp_vec):
                    print response
                    if float(response) > 0:
                        positive_trial_ind.append(i)
                    elif float(response) < 0:
                        negative_trial_ind.append(i)
                        
                print 'positive trials:'
                print positive_trial_ind
                print 'negative trials:'
                print negative_trial_ind
                
                print 'shuffling:'
                
                if len(positive_trial_ind) > len(negative_trial_ind):
                    min_limit = len(negative_trial_ind)
                    random.shuffle(positive_trial_ind)
                elif len(negative_trial_ind) > len(positive_trial_ind):
                    min_limit = len(positive_trial_ind)
                    random.shuffle(negative_trial_ind)
                elif len(negative_trial_ind) == len(positive_trial_ind):
                    min_limit = len(negative_trial_ind)
                    
                print 'positive trials:'
                print positive_trial_ind
                print 'negative trials:'
                print negative_trial_ind
                print 'limiting trial length: %s' % str(min_limit)
                    
                for i in range(min_limit):
                    positive_trial = temp_trials[positive_trial_ind[i]]
                    negative_trial = temp_trials[negative_trial_ind[i]]
                    self.design.append(positive_trial[self.m])
                    self.design.append(negative_trial[self.m])
                    self.Y.append(1)
                    self.Y.append(-1)
                
                print 'design length: %s ' % str(len(self.design))
                print 'response length: %s' % str(len(self.Y))
                
                
                # record of trial responses in text file:
                for j in range(self.reg_total_trials-1):
                    self.vecfile1.write(str(respvec[(j+1)*(self.reg_trial_trs)-respdiff-1])+'\n')
                    self.vecfile2.write(str(respvec[(j+1)*(self.reg_trial_trs)-respdiff-1])+'\n')
                #print self.Y
                    
        
        elif self.dynamic_iti:
            for (data,respvec,onsetvec) in zip(self.raw_data_list,self.resp_vecs,self.onset_vecs):
                onsetindices = np.nonzero(onsetvec)[0]
                if not self.lookback:
                    for ind in onsetindices:
                        trial = data[:,:,:,(ind+self.lag):(ind+self.reg_trial_trs+self.lag)]
                        if self.use_mask:
                            temp = np.array(trial[self.m])
                            pprint(temp.shape)
                            self.design.append(trial[self.m])
                        else:
                            trial = np.array(trial)
                            self.design.append(trial.flatten())
                        # response vector here should have every TR in trial marked with response!
                        self.Y.extend(respvec[ind])
                        print(respvec[ind])
                elif self.lookback:
                    for ind in onsetindices:
                        if not ind == 0:
                            trial = data[:,:,:,(ind+self.lag-self.lookback_trs):(ind+self.reg_trial_trs+self.lag)]
                            if self.use_mask:
                                self.design.append(trial[self.m])
                            else:
                                self.design.append(trial)
                            # response vector here should have every TR in trial marked with response!
                            self.Y.extend(respvec[ind])
        self.combined_data_vectors = True
    
    def normalize(self):
        self.design = np.array(self.design)
        #self.X_nonnorm = self.design
        #pprint(self.design.shape)
        #self.X_nonnorm = np.vstack(self.design)
        #pprint(self.X_nonnorm.shape)
        
        #temp = np.std(self.X_nonnorm,axis=0)
        #for x in temp:
        #    pprint(x)
        #self.X = (self.X_nonnorm - np.mean(self.X_nonnorm,axis=0))/np.std(self.X_nonnorm,axis=0)
        

        _design_zero_columns = (self.design**2).sum(0) == 0
        self.zero_mask = rr.selector(_design_zero_columns, self.design.shape[1:])
        # self.X = self.design
        
        self.X = rr.normalize(self.design,center=True,scale=True)
        self.p = self.X.primal_shape
        pprint(self.X)
        self.normalized = True
    
    def define_loss(self,set_coef=0.5):
        self.Y_signs = np.array(self.Y)
        self.Y_binary = (self.Y_signs + 1) / 2.
        self.quadratic_loss = rr.quadratic.affine(self.X,-self.Y_signs,coef=set_coef)
        self.logistic_loss = rr.logistic_loglikelihood.linear(self.X,successes=self.Y_binary,coef=set_coef)
        self.huber_loss = rr.huber_loss.linear(self.X,delta=0.3,coef=set_coef)
        #self.loss = rr.l2norm.affine(self.X,-self.Y_signs,lagrange=set_lagrange)
        self.loss = self.logistic_loss
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
                       coef_multiplier=0.001):
        # coef_multiplier was .0001 
        if loss is None:
            loss = self.loss
        if ridge is None:
            ridge = self.ridge
        if sparsity is None:
            #sparsity = self.sparsity_bound
            sparsity = self.sparsity
        if graphnet is None:
            graphnet = self.graphnet
            #graphnet = self.graphnet
        #set up the problem object:
        self.problem = rr.container(loss,ridge,sparsity,graphnet)
        self.problem.coefs = np.random.standard_normal(self.problem.coefs.shape) * coef_multiplier
        #set up the problem solver (FISTA):
        self.solver = rr.FISTA(self.problem)
        #set up problem debug as true:
        self.solver.debug = True
        self.problem_defined = True

    def solve_problem(self):
        #solve the problem:
        #try: 
        self.solver.fit(tol=self.set_tol,start_inv_step=self.inv_step,max_its=self.max_its)
        #grab the coefficients:
        self.solution = self.solver.composite.coefs
        #pprint('solution:')
        pprint('l1 norm: %f' % np.fabs(self.solution).sum())
        #pprint(self.solution.shape)
        #reshape the data!!

        #find the linear predictor, and predicted values
        Xbeta = self.X.linear_map(self.solution)
        #predicted values are determined by sign of Xbeta for squared error, logistic and robust graph net 
        #losses
        labels = np.sign(Xbeta)
        accuracy = (labels == self.Y_signs).sum() * 1. / labels.shape[0]
        print 'accuracy', accuracy

        if self.use_mask:
            self.solution_shaped = np.zeros((self.mask_shape[0],self.mask_shape[1],
                                             self.mask_shape[2],self.reg_prediction_tr_len))
            #_solution_with_zeros = np.zeros(self.m.shape)
            #_solution_with_zeros[~self._design_zero_columns] = 
            #self.solution_shaped[np.where(self.m)] = _solution_with_zeros
            self.solution_shaped[np.where(self.m)] = self.solution
        else:
            self.solution_shaped = self.solution.reshape(self.raw_data_shape[0],
                                                         self.raw_data_shape[1],
                                                         self.raw_data_shape[2],
                                                         self.reg_prediction_tr_len)
        self.problem_solved = True
    
    def output_nii(self):
        os.chdir(self.scripts_dir)
        #output_filename = 'rr_%(n)sn_r%(ridge)1.1e_s%(sparsity)1.1e_g%(graph)1.1e' % \
        #                  {'n':len(self.reg_subjects),'ridge':self.lambda2,'sparsity':self.lambda1,\
        #                   'graph':self.lambda3}
        output_filename = 'reg13_paperparams'
        if self.use_mask:
            newnii = nib.Nifti1Image(self.solution_shaped,self.mask_affine)
        else:
            newnii = nib.Nifti1Image(self.solution_shaped,self.raw_affine)
        general_cleaner(output_filename+'.nii',0)
        general_cleaner(output_filename,1)
        newnii.to_filename(output_filename+'.nii')
        #EXTRA:
        shell_command(['3dcopy',output_filename+'.nii',output_filename])
        shell_command(['adwarp','-apar','TT_N27+tlrc','-dpar',output_filename+'+orig','-overwrite'])
        self.output_complete = True
        
    def try_output(self):
        output_filename = 'temp_output'
        shaped = np.zeros((self.mask_shape[0],self.mask_shape[1],self.mask_shape[2],
                           self.reg_prediction_tr_len))
        shaped[np.where(self.m)] = self.X[0,:]
        newnii = nib.Nifti1Image(shaped,self.mask_affine)
        newnii.to_filename(output_filename+'.nii')
    
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
            self.vecfile1.close()
            self.vecfile2.close()
        else:
            print '\nERROR: Impossible to run() without initializing variables.\n'
        

    
    
    
    
    
    
    
    
    
    
    
    
