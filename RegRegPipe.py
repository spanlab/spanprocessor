#!/usr/bin/env python

from pprint import pprint
import subprocess
import glob
import sys, os
import random
import itertools
import simplejson
import math
import numpy as np
import numpy.lib.format as npf
import scipy as sp
from scipy import sparse
from scipy import io
import nibabel as nib
import regreg.api as rr
from regreg.affine import selector
import regreg.mask as mask
from mono_utility import (general_cleaner, shell_command)


class RegRegPipe(object):
    def __init__(self):
        
        self.required_vars = ['reg_nifti_name','reg_mask_name','reg_resp_vec_name',
                              'reg_onset_vec_name','reg_response_tr','reg_subjects',
                              'reg_total_trials','reg_prediction_tr_len','reg_mask_dir',
                              'lag','reg_experiment_trs','reg_trial_trs','scripts_dir',
                              'dynamic_iti','lambda1','bound1','lambda2','lambda3','bound3',
                              'inv_step','set_tol','max_its','lookback','lookback_trs',
                              'use_mask','output_filename','random_seed','downsample_type',
                              'warm_start','reg_save_dir','crossvalidation_folds']
        
        
    
    def initialize_variables(self,var_dict):

        self.var_dict = var_dict
        
        for key, value in var_dict.items():
            setattr(self,key,value)
            
        for var_name in self.required_vars:
            if not var_name in var_dict:
                print 'WARNING: %s was NOT included in the variable dictionary!\n' % var_name
                print 'Not including %s may or may not break the pipeline.\n' % var_name
                print 'Know what you are doing!\n'
                setattr(self,var_name,False)
        

        for attribute in ('raw_data_shape','raw_data_list','raw_affine','design',
                          'Y','resp_vecs','onset_vecs'):
            #if getattr(self,attribute,None):
            setattr(self,attribute,[])
    
        self.top_dir = os.getcwd()
        self.save_dir = os.path.join(self.top_dir,self.reg_save_dir)
        self.bin_dir = os.path.join(self.save_dir,'reg_bin')
        self.records_dir = os.path.join(self.save_dir,'records')
        
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)
        if not os.path.exists(self.bin_dir):
            os.mkdir(self.bin_dir)
        if not os.path.exists(self.records_dir):
            os.mkdir(self.records_dir)
        
        if type(self.reg_nifti_name) != type ([]):
            self.reg_nifti_name = [self.reg_nifti_name]
        if type(self.reg_resp_vec_name) != type([]):
            self.reg_resp_vec_name = [self.reg_resp_vec_name]
            
        if not getattr(self,'crossvalidation_type',None):
            setattr(self,'crossvalidation_type','subject')
            
        self.total_nifti_files = 0
        self.subject_trial_indices = {}
        
        #self.coefs_name = self.output_filename+'_coefs.npy'
        #self.coefs_name = 'reupd_coefs.npy'
        
        self.coefs_name = 's:%s_r:%s_g:%s_l3:%s_coefs.npy' % (str(float(self.bound1)),
                                                           str(float(self.bound2)),
                                                           str(float(self.bound3)),
                                                           str(float(self.lambda3)))
        
        self.memmap_name = 'raw_data.npy'
        self.sparse_matrix_name = 'sparse_matrix.mat'
        
        # results collectors:
        self.l1_norms = []
        self.l2_norms = []
        self.graphnet_norms = []
        self.accuracies = []
        
        
        np.random.seed(self.random_seed)
        random.seed(self.random_seed)
        
        self.variables_initialized = True
        
        
    def load_data_matrix(self):
        
        memmap_path = os.path.join(self.bin_dir,self.memmap_name)
        affine_path = os.path.join(self.bin_dir,'raw_affine.npy')
        if os.path.exists(memmap_path):
            
            print 'loading in '+self.memmap_name
            
            self.raw_data_list = npf.open_memmap(memmap_path,mode='r',dtype='float32')
            #self.raw_data_list = np.load(memmap_path)

            print 'shape of loaded memmap:'
            print self.raw_data_list.shape
            
            self.loaded_warm_start = True
            
        else:
            print 'no file of name '+self.memmap_name+' to load.'
            print 'aborting memmap load'
            
        if os.path.exists(affine_path):
            self.raw_affine = np.load(affine_path)
        else:
            return False
        
        return True



    def _coef_name_parser(self,name):
        name = name.strip('/').split('_')
        s = float(name[0].strip('s:'))
        r = float(name[1].strip('r:'))
        g = float(name[2].strip('g:'))
        l3 = float(name[3].strip('l3:'))
        return (s,r,g,l3)
        
        
        
    def load_coefs(self):

        coefs_path = os.path.join(self.bin_dir,self.coefs_name)

        if os.path.exists(coefs_path):
            self.preloaded_coefs = np.load(coefs_path)
            print 'Shape of problem coefs: '
            print self.preloaded_coefs.shape
            return True
        else:
            allcoefs = glob.glob(self.bin_dir+'/*coefs.npy')
            if not allcoefs:
                self.preloaded_coefs = np.array([])
                print 'No recent coefs saved/found.'
                return False
            else:
                match_calc = []
                (s,r,g,l3) = self._coef_name_parser(self.coefs_name)
                for match in allcoefs:
                    match = os.path.split(match)[1]
                    (cur_s,cur_r,cur_g,cur_l3) = self._coef_name_parser(match)
                    match_calc.append(abs(s-cur_s) + abs(r-cur_r) + abs(g-cur_g) + abs(l3-cur_l3))
                min_ind = match_calc.index(min(match_calc))
                best_match = allcoefs[min_ind]
                print 'Best match for coefs:  %s' % best_match
                self.preloaded_coefs = np.load(best_match)
                print 'Shape of problem coefs: '
                print self.preloaded_coefs.shape
                return True
                
             

    def __load_nifti(self,nifti):
        image = nib.load(nifti)
        shape = image.get_shape()
        idata = image.get_data()
        affine = image.get_affine()
        return [idata,affine,shape]
        
        
        
    def create_data_matrix(self, save_memmap=True, nuke=True):
        
        raw_path = os.path.join(self.bin_dir,self.memmap_name)
        
        if nuke and os.path.exists(raw_path):
            os.remove(raw_path)
            
        if save_memmap:            
            # We need to determine how many nifti files there are in total to
            # determine the shape of the memmap:
            
            brainshape = []

            for subject in self.reg_subjects:
                sub_path = os.path.join(self.top_dir,subject)
                for nifti_name in self.reg_nifti_name:
                    nifti_path = os.path.join(sub_path,nifti_name)
                    if os.path.exists(nifti_path):
                        self.total_nifti_files += 1
                        if not brainshape:
                            [tempdata,tempaffine,brainshape] = self.__load_nifti(nifti_path)
                
            # Allocate the .npy memmap according to its size:
            
            memmap_shape = (self.total_nifti_files,brainshape[0],brainshape[1],brainshape[2],
                            brainshape[3])
            
            print 'Determined memmap shape:'
            print memmap_shape
            print 'Allocating the memmap...'
            
            self.raw_data_list = npf.open_memmap(raw_path,mode='w+',dtype='float32',
                                                 shape=memmap_shape)
            
            print 'Succesfully allocated memmap... memmap shape:'
            pprint(self.raw_data_list.shape)
            
        
        nifti_iter = 0
        for subject in self.reg_subjects:
            sub_path = os.path.join(self.top_dir,subject)
            print sub_path
            print subject
            print os.getcwd()
            
            for nifti_name in self.reg_nifti_name:
                nifti_path = os.path.join(sub_path,nifti_name)
                pprint(nifti_name)
                if os.path.exists(nifti_path):
                    [idata,affine,ishape] = self.__load_nifti(nifti_path)
                    pprint(ishape)
                    
                    if save_memmap:
                        print 'Appending idata to memmap at: %s' % str(nifti_iter)
                        self.raw_data_list[nifti_iter] = np.array(idata)
                        self.subject_trial_indices[nifti_iter] = []
                        nifti_iter += 1
                    
                    if self.reg_experiment_trs == False:
                        self.reg_experiment_trs = len(idata[3])
                        
                    if self.reg_total_trials == False:
                        if self.reg_trial_trs:
                            self.reg_total_trials = self.reg_experiment_trs/self.reg_trial_trs

                    if self.raw_affine == []:
                        self.raw_affine = affine
                        affine_path = os.path.join(self.bin_dir,'raw_affine.npy')
                        np.save(affine_path,self.raw_affine)
                        
                    if self.raw_data_shape == []:
                        self.raw_data_shape = ishape
                        pprint(ishape)
                        
        
        
        
    def __parse_vector(self,vector):
        vfile = open(vector,'rb')
        vlines = vfile.readlines()
        varray = np.zeros(shape=len(vlines))
        
        for i in range(len(vlines)):
            vline = int(vlines[i].strip('\n'))
            if vline == 1 or vline == -1:
                varray[i] = vline

        return varray
    
    
        
    def parse_resp_vecs(self):

        for subject in self.reg_subjects:
            print self.top_dir
            sub_path = os.path.join(self.top_dir,subject)
            print sub_path
            
            for resp_vec in self.reg_resp_vec_name:
                vec_path = os.path.join(sub_path,resp_vec)
                if os.path.exists(vec_path):
                    resp_array = self.__parse_vector(vec_path)
                    self.resp_vecs.append(resp_array)
                    
            if self.dynamic_iti:
                onset_vec_path = os.path.join(sub_path,self.reg_onset_vec_name)
                onset_vec = self.__parse_vector(onset_vec_path)
                self.onset_vecs.append(onset_vec)
            
        
        
    
    def create_reg_mask(self):
        
        if self.reg_mask_dir:
            mask_path = os.path.join(self.top_dir,self.reg_mask_dir)
        else:
            print 'Using scripts directory as default location for masked dataset...'
            mask_path = os.path.join(self.top_dir,self.scripts_dir)
            
        mask_name_path = os.path.join(mask_path,self.reg_mask_name)
        
        [self.mask_data,self.mask_affine,self.mask_shape] = self.__load_nifti(mask_name_path)
        
        self.m = np.zeros([self.mask_shape[0],self.mask_shape[1],\
                           self.mask_shape[2],self.reg_prediction_tr_len],np.bool)
        
        for i in range(self.reg_prediction_tr_len):
            self.m[:,:,:,i] = self.mask_data[:,:,:]
                
        
        
    def combine_data_vectors(self):
        
        tr_selection = [x-1 for x in self.trs_of_interest]
        
        subject_trials = {}
            
        if not self.lookback:
            self.lookback_trs = 0
        
       
        if not self.dynamic_iti:

            for s,(data,respvec) in enumerate(zip(self.raw_data_list,self.resp_vecs)):
                
                subject_trials[s] = []                
                
                onsetindices = [x*self.reg_trial_trs for x in range(self.reg_total_trials)]
                respindices = respvec[[onset+(self.reg_response_tr-1) for onset in onsetindices]]
                
                #print onsetindices
                #print respindices
                
                if len(onsetindices) != len(respindices):
                    print 'ERROR: Onset and Response indices not the same length!!'
                    print onsetinds
                    print respinds
                
                for i,ind in enumerate(onsetindices):
                    if respindices[i] != 0:
                        trs = [ind+tr+self.lag-self.lookback_trs for tr in tr_selection]
                        trial = data[:,:,:,trs]
                        resp = respindices[i]
                        subject_trials[s].append([resp,trial])
                            

        elif self.dynamic_iti:

            for s,(data,respvec,onsetvec) in enumerate(zip(self.raw_data_list,self.resp_vecs,self.onset_vecs)):

                subject_trials[s] = []
                
                onsetindices = np.nonzero(onsetvec)[0]
                respindices = respvec[onsetindices]
                
                if len(onsetindices) != len(respindices):
                    print 'ERROR: Onset indices and response vector different lengths.'
                    print onsetindices
                    print respindices

                for i,ind in enumerate(onsetindices):
                    if not self.lookback or not i == 0:
                        if respindices[i] != 0:
                            trs = [ind+tr+self.lag-self.lookback_trs for tr in tr_selection]
                            trial = data[:,:,:,trs]
                            resp = respindices[i]
                            subject_trials[s].append([resp,trial])


        if not self.downsample_type:

            for subj,trials in subject_trials.items():
                self.subject_trial_indices[subj] = []
                
                for resp,trial in trials:
                    self.subject_trial_indices[subj].append(len(self.design))
                    self.design.append(trial[self.m])
                    self.Y.append(resp)


        elif self.downsample_type == 'group':
            
            positive_trials = []
            negative_trials = []
            
            for subj,trials in subject_trials.items():
                self.subject_trial_indices[subj] = []
                for [resp,trial] in trials:
                    if float(resp) > 0:
                        positive_trials.append([subj,trial[self.m]])
                    elif float(resp) < 0:
                        negative_trials.append([subj,trial[self.m]])
            
            
            random.shuffle(positive_trials)
            random.shuffle(negative_trials)
            
            if not self.with_replacement:
                for i in range(min(len(positive_trials), len(negative_trials))):
                    [psubj,ptrial] = positive_trials[i]
                    [nsubj,ntrial] = negative_trials[i]
                    self.subject_trial_indices[psubj].append(len(self.design))
                    self.design.append(ptrial)
                    self.subject_trial_indices[nsubj].append(len(self.design))
                    self.design.append(ntrial)
                    self.Y.append(1)
                    self.Y.append(-1)
                    
            elif self.with_replacement:
                print 'subject pos+neg trials: %s' % str(len(positive_trials)+len(negative_trials))
                for i in range((len(positive_trials) + len(negative_trials))/2):
                    if i < len(positive_trials):
                        [psubj,ptrial] = positive_trials[i]
                    else:
                        [psubj,ptrial] = positive_trials[random.randrange(0,len(positive_trials))]
                    if i < len(negative_trials):
                        [nsubj,ntrial] = negative_trials[i]
                    else:
                        [nsubj,ntrial] = negative_trials[random.randrange(0,len(negative_trials))]
                    self.subject_trial_indices[psubj].append(len(self.design))
                    self.design.append(ptrial)
                    self.subject_trial_indices[nsubj].append(len(self.design))
                    self.design.append(ntrial)
                    self.Y.append(1)
                    self.Y.append(-1)
                    

            print 'min limit: %s' % str(min(len(positive_trials),len(negative_trials)))
            print 'design length: %s ' % str(len(self.design))
            print 'response length: %s' % str(len(self.Y))
            print 'yes responses: %s' % str(self.Y.count(1))
            print 'no responses: %s' % str(self.Y.count(-1))
            print 'response skew (positive/negative): %s' % str(sum(self.Y))

        
        elif self.downsample_type == 'subject':
            
            for subj,trials in subject_trials.items():
                self.subject_trial_indices[subj] = []
                
                subject_positives = []
                subject_negatives = []
                
                for [resp,trial] in trials:
                    if float(resp) > 0:
                        subject_positives.append(trial[self.m])
                    elif float(resp) < 0:
                        subject_negatives.append(trial[self.m])
            
                random.shuffle(subject_positives)
                random.shuffle(subject_negatives)
                
                if min(len(subject_positives), len(subject_negatives)) == 0:
                    del self.subject_trial_indices[subj]
                
                else:
                    if not self.with_replacement:
                        for i in range(min(len(subject_positives), len(subject_negatives))):
                            self.subject_trial_indices[subj].append(len(self.design))
                            self.design.append(subject_positives[i])
                            self.subject_trial_indices[subj].append(len(self.design))
                            self.design.append(subject_negatives[i])
                            self.Y.append(1)
                            self.Y.append(-1)
                            
                    elif self.with_replacement:
                        print 'subject pos+neg trials: %s' % str(len(subject_positives)+len(subject_negatives))
                        for i in range((len(subject_positives) + len(subject_negatives))/2):
                            self.subject_trial_indices[subj].append(len(self.design))
                            if i < len(subject_positives):
                                self.design.append(subject_positives[i])
                            else:
                                self.design.append(subject_positives[random.randrange(0,len(subject_positives))])
                            self.subject_trial_indices[subj].append(len(self.design))
                            if i < len(subject_negatives):
                                self.design.append(subject_negatives[i])
                            else:
                                self.design.append(subject_negatives[random.randrange(0,len(subject_negatives))])
                            self.Y.append(1)
                            self.Y.append(-1)
                                
                
                print 'min limit: %s' % str(min(len(subject_positives), len(subject_negatives)))
                print 'design length: %s ' % str(len(self.design))
                print 'response length: %s' % str(len(self.Y))
                print 'yes responses: %s' % str(self.Y.count(1))
                print 'no responses: %s' % str(self.Y.count(-1))
                print 'response skew (positive/negative): %s' % str(sum(self.Y))
        
        
            
    def prepare_crossvalidation(self,leave_mod_in=False):
        
        self.crossval_train = []
        self.crossval_test = []
        
        # Function to split data into equal sized groups:
        chunker = lambda inds,size: [inds[i:i+size] for i in range(0,len(inds),size)]
        
        if not self.crossvalidation_folds or (self.crossvalidation_folds == 1):
            
            return False
        
        elif self.crossvalidation_type == 'subject':
            
            
            # Calculate number of niftis that do not fit in equal folds:
            extra_brains = len(self.subject_trial_indices) % self.crossvalidation_folds
            
            # If there are extra, determine whether they will be tested on or
            # left out.
            if extra_brains:
                print 'Crossvalidation subsample size not a factor of the subject/brain array.'
                if leave_mod_in:
                    print "'Extra' brains will be added to each test set."
                else:
                    print "'Extra' brains will be left out of the analysis (chosen at random)"
            
            
            # Shuffle the brain data
            shuffled_brain_inds = self.subject_trial_indices.keys()
            random.shuffle(shuffled_brain_inds)
            
            # Divide brain data into extra brains and crossvalidation folds:
            crossval_extra = shuffled_brain_inds[0:extra_brains]
            shuffled_brain_inds = shuffled_brain_inds[extra_brains:]
            
            # Divide the data into as many equal sized groups as there are specified folds,
            # group size defined by size of brain data divided by number of folds:
            crossval_sets = chunker(shuffled_brain_inds,
                                    (len(shuffled_brain_inds)/self.crossvalidation_folds))
            
            print crossval_sets
            
            # zip up the crossvalidation groups with group indices:
            sets_inds = zip(crossval_sets,range(len(crossval_sets)))

            # get possible permutations of crossvalidation groups when leaving
            # one out:
            set_permutations = itertools.combinations(sets_inds,len(crossval_sets)-1)
            
            # Iterate through the permutations and assign test and training brain
            # data indices:
            for permutation in set_permutations:
                current_inds = []
                train_set = []
                test_set = []
                for brains,ind in permutation:
                    current_inds.append(ind)
                    train_set.extend(brains)
                for i in range(len(crossval_sets)):
                    if i not in current_inds:
                        test_set = crossval_sets[i]
                        if crossval_extra and leave_mod_in:
                            test_set.extend(crossval_extra)
                
                print train_set
                print test_set
                            
                train_trials = []
                test_trials = []
                
                # assign the actual indices of trials in the design matrix to
                # the crossvalidation test and training indices:
                for brain in train_set:
                    train_trials.extend(self.subject_trial_indices[brain])
                for brain in test_set:
                    test_trials.extend(self.subject_trial_indices[brain])
                    
                #print '\nLength of training trials:'
                #print len(train_trials)
                #print '\nLength of test trials:'
                #print len(test_trials)
                #print 'check overlap...'
                #print any([x for x in train_trials if x in test_trials])
                    
                self.crossval_train.append(train_trials)
                self.crossval_test.append(test_trials)
                
            return True
        
        elif self.crossvalidation_type == 'trial':
            
            # Calculate number of trials that do not fit in equal folds:
            extra_trials = len(self.design) % self.crossvalidation_folds
            
            # If there are extra, determine whether they will be tested on or
            # left out.
            if extra_trials:
                print 'Crossvalidation subsample size not a factor of the trial array.'
                if leave_mod_in:
                    print "'Extra' trials will be added to each test set."
                else:
                    print "'Extra' trials will be left out of the analysis (chosen at random)"
            
            
            # Shuffle the trial data
            shuffled_trial_inds = range(len(self.design))
            random.shuffle(shuffled_trial_inds)
            
            # Divide trials into extra trials and crossvalidation folds:
            crossval_extra = shuffled_trial_inds[0:extra_trials]
            shuffled_trial_inds = shuffled_trial_inds[extra_trials:]
            
            
            # Divide the data into as many equal sized groups as there are specified folds,
            # group size defined by size of brain data divided by number of folds:
            crossval_sets = chunker(shuffled_trial_inds,
                                    (len(shuffled_trial_inds)/self.crossvalidation_folds))
            
            #print crossval_sets
            
            # zip up the crossvalidation groups with group indices:
            sets_inds = zip(crossval_sets,range(len(crossval_sets)))

            # get possible permutations of crossvalidation groups when leaving
            # one out:
            set_permutations = itertools.combinations(sets_inds,len(crossval_sets)-1)
            
            # Iterate through the permutations and assign test and training trials:
            for permutation in set_permutations:
                current_inds = []
                train_set = []
                test_set = []
                for trials,ind in permutation:
                    current_inds.append(ind)
                    train_set.extend(trials)
                for i in range(len(crossval_sets)):
                    if i not in current_inds:
                        test_set = crossval_sets[i]
                        if crossval_extra and leave_mod_in:
                            test_set.extend(crossval_extra)
                
                print len(train_set)
                print len(test_set)
                
                self.crossval_train.append(train_set)
                self.crossval_test.append(test_set)
                
                train_trials = []
                test_trials = []
                
                
            return True
            
            
            

    def normalize(self,crossvalidate=False, train_trials=False, test_trials=False):
        #if not hasattr(self, 'X'):
        
        if not crossvalidate:
            design = np.array(self.design)
            # adding a global intercept as the first column
            self.design = np.hstack([np.ones(design.shape[0]), design])
            self.X = rr.normalize(self.design,center=True,scale=True,intercept_column=0)
            self.Y_signs = np.array(self.Y)
            self.Y_binary = (self.Y_signs + 1) / 2.
            
        else:

            train_design = np.array([self.design[i] for i in train_trials])
            test_design = np.array([self.design[i] for i in test_trials])
            
            self.X = rr.normalize(train_design,center=True,scale=True)
            self.X_test = rr.normalize(test_design,center=True,scale=True)
            
            print len(train_trials)
            print len(self.Y)
            
            self.Y_train = [self.Y[i] for i in train_trials]
            self.Y_test = [self.Y[i] for i in test_trials]
            
            self.Y_signs = np.array(self.Y_train)
            self.Y_binary = (self.Y_signs + 1) / 2.
            
            self.Y_signs_test = np.array(self.Y_test)
            self.Y_binary_test = (self.Y_signs_test + 1) / 2
            
        self.p = self.X.primal_shape
        
    
    @property
    def D(self):
        
        if not hasattr(self, '_D'):
            sparse_path = os.path.join(self.bin_dir,self.sparse_matrix_name)

            if os.path.exists(sparse_path):
                self._D = io.loadmat(sparse_path)['D']

            else:
                pprint("Couldn't find the file -- creating D.")
                self.adj = mask.prepare_adj(self.m,numx=1,numy=1,numz=1,numt=1)
                self._D = sparse.csr_matrix(mask.create_D(self.adj))
                pprint(self._D)
                io.savemat(sparse_path, {'D':self.D})
        return self._D
                
    
    def logistic_loss(self):
        return rr.logistic_loglikelihood.linear(self.X,successes=self.Y_binary)

    def quadratic_loss(self):
        return rr.quadratic.affine(self.X,-self.Y_signs,coef=0.5)

    def huber_loss(self):
        return rr.huber_loss.linear(self.X,delta=0.3,coef=0.5)
        
    @property
    def ridge_bound(self):
        return rr.l2norm(self.p,bound=self.bound2)

    @property
    def ridge_bound_smooth(self):
        return rr.smoothed_atom(self.ridge_bound, 0.001)

    @property
    def ridge(self):
        if self.lambda2 > 0:
            return rr.quadratic(self.p,bound=self.lambda2)
        else:
            return None
        
    @property
    def sparsity(self):
        if self.lambda1 > 0:
            return rr.l1norm(self.p, lagrange=self.lambda1)
        else:
            return None

    @property
    def sparsity_bound(self):
        return rr.l1norm(self.p, bound=self.bound1)
    
    @property
    def graphnet(self):
        if self.lambda3 > 0:
            return rr.quadratic.linear(self.D,coef=self.lambda3)
        else:
            return None

    @property
    def graphnet_bound(self):
        return rr.l2norm.linear(self.D,bound=self.bound3)

    @property
    def graphnet_bound_smooth(self):
        return rr.smoothed_atom(self.graphnet_bound, epsilon=0.001)

    @property
    def penalty(self):
        ps = [getattr(self, p) for p in self.penalties]
        return [p for p in ps if p is not None]

    def problem(self):
        loss = {'logistic': self.logistic_loss(),
                'quadratic': self.quadratic_loss(),
                'huber': self.huber_loss()}[self.loss]

        return rr.container(loss, *self.penalty)
        

    def solve_problem(self, crossvalidate=False, coef_multiplier=0.001, debug=False):
        
        problem = self.problem()
        #set up the problem solver (FISTA):
        
        
        if not self.warm_start or not self.preloaded_coefs.any():
            
            print 'Loading in random coefficients: '
            problem.coefs[:] = np.random.standard_normal(problem.coefs.shape) * coef_multiplier
            
        elif self.warm_start and self.preloaded_coefs.any():
            #problem.coefs[:] = self.preloaded_coefs
            
            print 'Loading in random coefficients: '
            problem.coefs[:] = np.random.standard_normal(problem.coefs.shape) * coef_multiplier
            
        #if crossvalidate:
        #    print 'Loading in prior CV coefficients.'
        #    if hasattr(self, 'solution'):
        #        problem.coefs[:] = self.solution

        print 'Problem coefficients shape: '
        print problem.coefs.shape
        
        #solve the problem:
        solver = rr.FISTA(problem)

        while True:
            try:
                solver.fit(tol=self.set_tol,start_inv_step=self.inv_step,max_its=self.max_its, debug=debug)
                break
            except KeyboardInterrupt:
                r = raw_input('[S]ave coefficients and continue or [B]reak? S/B').lower()
                if r == 's':
                    coefs_path = os.path.join(self.bin_dir,self.coefs_name)
                    np.save(coefs_path,solver.composite.coefs)
                raise KeyboardInterrupt
                    
        #grab the coefficients: but not the intercept in column 0
        self.solution = solver.composite.coefs
        
        coefs_path = os.path.join(self.bin_dir,self.coefs_name)
        # save the coefficients
        np.save(coefs_path,self.solution)

        l1_norm = np.fabs(self.solution).sum()
        l2_norm = np.linalg.norm(self.solution)
        graphnet_norm = np.linalg.norm(self.D * self.solution)
        
        pprint('l1 norm: %f' % l1_norm)
        pprint('l2 norm: %f' % l2_norm)
        pprint('graphnet norm: %f' % graphnet_norm)
        
        self.l1_norms.append(l1_norm)
        self.l2_norms.append(l2_norm)
        self.graphnet_norms.append(graphnet_norm)


        if crossvalidate:
            
            Xbeta_test = self.X_test.linear_map(self.solution)
            
            labels = np.sign(Xbeta_test)
            
            fold_accuracy = (labels == self.Y_signs_test).sum() * 1. / labels.shape[0]

            print 'Fold: (%d Y, %d N)' % ((labels == 1).sum(), (labels == -1).sum())
            print 'Fold Accuracy: %d/%d= %0.1f%%' % ((labels == self.Y_signs_test).sum(), labels.shape[0], fold_accuracy*100)
            
            self.accuracies.append(fold_accuracy)
            
        else:
            
            #find the linear predictor, and predicted values
            Xbeta = self.X.linear_map(self.solution)
            
            #predicted values are determined by sign of Xbeta for squared error, logistic and robust graph net 
            #losses
            labels = np.sign(Xbeta)
            print labels.shape
            print self.Y_signs.shape
            print (labels == self.Y_signs).sum()
            
            accuracy = (labels == self.Y_signs).sum() * 1. / labels.shape[0]
            print 'accuracy', accuracy
            
            self.accuracies.append(accuracy)

            # Prepare the solution for outputting to nifti:
            
            if self.use_mask:
                
                self.solution_shaped = np.zeros((self.mask_shape[0],self.mask_shape[1],
                                                 self.mask_shape[2],self.reg_prediction_tr_len))
                # here, we remove the first column which was the intercept
                self.solution_shaped[np.where(self.m)] = self.solution[1:]
            
            else:
                self.solution_shaped = self.solution[1:].reshape(self.raw_data_shape[0],
                                                                 self.raw_data_shape[1],
                                                                 self.raw_data_shape[2],
                                                                 self.reg_prediction_tr_len)
        
        
        
    '''
    FOR FUTURE:
    Create map that displays accuracy per voxel.
    
    Calculate the accuracy per voxel by multiplying coefficient of voxel by
    activation in that voxel.
    
    Multiply the value of that voxel by the number of coefficients in the solution
    that are not zero. (as if the voxel/coefficient is the only one in the brain;
    we will not sum the coefficients later)    
    
    '''
    
    def output_nii(self):

        output_path = os.path.join(self.save_dir,self.output_filename)
        
        #if self.use_mask:
        #    newnii = nib.Nifti1Image(self.solution_shaped,self.mask_affine)
        #else:
        newnii = nib.Nifti1Image(self.solution_shaped,self.raw_affine)
            
        general_cleaner(output_path+'.nii',0)
        general_cleaner(output_path,1)
        newnii.to_filename(output_path+'.nii')
        #EXTRA:
        shell_command(['3dcopy',output_path+'.nii',output_path])
        shell_command(['adwarp','-apar',os.path.join(self.save_dir,'TT_N27+tlrc'),'-dpar',output_path+'+orig','-overwrite'])
        self.output_complete = True
        
    def _median(self,x):
        x = sorted(x)
        i = len(x)
        if not i % 2:
            return (x[(i/2)-1]+x[i/2])/2.0
        else:
            return x[i/2]
        
    def log_session(self):
        
        self.mean_accuracy = sum(self.accuracies)/len(self.accuracies)
        self.median_accuracy = self._median(self.accuracies)
            
        print 'Mean Accuracy:  %s' % str(self.mean_accuracy)
        print 'Median Accuracy:  %s' % str(self.median_accuracy)
        
        log_dict = {'set_bound1':self.bound1,'set_bound2':self.bound2,'set_bound3':self.bound3,
                    'set_lambda3':self.lambda3,'tolerance':self.set_tol,'output':self.output_filename,
                    'random_seed':self.random_seed,'downsample_type':self.downsample_type,
                    'crossvalidation_folds':self.crossvalidation_folds,
                    'l1_norms':self.l1_norms,'l2_norms':self.l2_norms,
                    'graphnet_norms':self.graphnet_norms,'accuracies':self.accuracies,
                    'mean_accuracy':self.mean_accuracy,
                    'median_accuracy':self.median_accuracy}
        
        json_path = os.path.join(self.records_dir,self.output_filename+'.json')
        
        jsonfile = open(json_path,'w')
        simplejson.dump(log_dict,jsonfile)
        jsonfile.close()
        
        pprint(log_dict)
        
        
    
    def run(self):
        
        if self.variables_initialized:
            data_found = False
            
            self.create_reg_mask() 
            print 'done with mask'
            if self.warm_start:
                data_found = self.load_data_matrix()
                coefs_found = self.load_coefs()
            if not self.warm_start or not data_found:
                self.create_data_matrix()
                
            self.parse_resp_vecs()
            self.combine_data_vectors()
            
            cv_flag = self.prepare_crossvalidation()
            
            print 'RAW AFFINE:'
            pprint(self.raw_affine)
            
            if cv_flag:
                for train,test in zip(self.crossval_train,self.crossval_test):
                    self.normalize(crossvalidate=True, train_trials=train, test_trials=test)
                    self.solve_problem(crossvalidate=True, debug=True)
            else:
                self.normalize()    
                self.solve_problem(debug=True)
                self.output_nii()
                
            self.log_session()

            
        else:
            print '\nERROR: Impossible to run() without initializing variables.\n'
        

    
    
    
    
    
    
    
    
    
    
    
    
