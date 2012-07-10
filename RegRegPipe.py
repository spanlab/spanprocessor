#!/usr/bin/env python

from pprint import pprint
import subprocess
import glob, gc
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





class RRData(object):
    
    def __init__(self, vars):
        super(RRData, self).__init__()
        self._instantiate_vars(vars)

        
    def _instantiate_vars(self, vars):
        self.vars = vars
        
        for key, value in self.vars.items():
            setattr(self, key, value)
            
        for attribute in ('raw_data_shape','raw_data_list','raw_affine','design',
                          'Y','resp_vecs','onset_vecs'):
            setattr(self,attribute,[])
            
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
            
        self.subject_trial_indices = {}
        
        self.total_nifti_files = 0
        
        
    def load_data_matrix(self):
        
        memmap_path = os.path.join(self.bin_dir,self.memmap_name)
        affine_path = os.path.join(self.bin_dir,self.affine_name)
        if os.path.exists(memmap_path):
            
            print 'loading in '+self.memmap_name
            
            self.raw_data_list = npf.open_memmap(memmap_path,mode='r',dtype='float32')

            print 'shape of loaded memmap:'
            print self.raw_data_list.shape
            
        else:
            print 'no file of name '+self.memmap_name+' to load.'
            print 'aborting memmap load'
            
        if os.path.exists(affine_path):
            self.raw_affine = np.load(affine_path)
        else:
            return False
        
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

            # Iterate niftis by subjects; add total niftis together; get the
            # shape of the brain from one of the niftis
            for subject in self.reg_subjects:
                sub_path = os.path.join(self.top_dir,subject)
                for nifti_name in self.reg_nifti_name:
                    nifti_path = os.path.join(sub_path,nifti_name)
                    if os.path.exists(nifti_path):
                        self.total_nifti_files += 1
                        if not brainshape:
                            [tempdata,tempaffine,brainshape] = self.__load_nifti(nifti_path)
                
            # Allocate the .npy memmap according to the brain shape:
            #memmap_shape = (self.total_nifti_files,brainshape[0],brainshape[1],brainshape[2],
            #                brainshape[3])
            
            
            # Allocate the .npy memmap according to the mask shape (and brain TRs):
            memmap_shape = (self.total_nifti_files, self.mask_shape[0], self.mask_shape[1],
                            self.mask_shape[2], brainshape[3])
            
            # Create a mask for all the TRs (mask before trial assignment)
            # This will hopefully decrease the size of the memmap
            self.full_mask = np.zeros([self.mask_shape[0],self.mask_shape[1],
                                       self.mask_shape[2],brainshape[3]],np.bool)
             
            for i in range(brainshape[3]):
                self.full_mask[:,:,:,i] = self.mask_data[:,:,:]
            
            
            print 'Determined memmap shape:'
            print memmap_shape
            print 'Allocating the memmap...'
            
            self.raw_data_list = npf.open_memmap(raw_path,mode='w+',dtype='float32',
                                                 shape=memmap_shape)
            
            print 'Succesfully allocated memmap... memmap shape:'
            pprint(self.raw_data_list.shape)
            
        
        # Iterate niftis by subject; add brain data from nifti to raw data array
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
                        idata = np.array(idata)
                        idata = idata[self.full_mask]
                        self.raw_data_list[nifti_iter] = np.array(idata)
                        self.subject_trial_indices[nifti_iter] = []
                        nifti_iter += 1
                    
                    if not getattr(self, 'reg_experiment_trs', False) or self.reg_experiment_trs == False:
                        self.reg_experiment_trs = len(idata[3])
                        
                    if self.reg_total_trials == False:
                        if self.reg_trial_trs:
                            self.reg_total_trials = self.reg_experiment_trs/self.reg_trial_trs

                    if self.raw_affine == []:
                        self.raw_affine = affine
                        affine_path = os.path.join(self.bin_dir,self.affine_name)
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
        
        print 'creating/loading mask'
        
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
        
        self.subject_trials = {}
            
        if not self.lookback:
            self.lookback_trs = 0
        
       
        if not self.dynamic_iti:
            print 'length of raw data list: %s' % str(len(self.raw_data_list))
            print 'length of response vectors: %s' % str(len(self.resp_vecs))

            for s,(data,respvec) in enumerate(zip(self.raw_data_list,self.resp_vecs)):
                
                self.subject_trials[s] = []                
                
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
                        self.subject_trials[s].append([resp,trial])
                                                    

        elif self.dynamic_iti:

            for s,(data,respvec,onsetvec) in enumerate(zip(self.raw_data_list,self.resp_vecs,self.onset_vecs)):

                self.subject_trials[s] = []
                
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
                            self.subject_trials[s].append([resp,trial])


    
    def free_raw_data(self):
        self.raw_data_list = None
        del(self.raw_data_list)
        gc.collect()



    def generate_design_matrix(self):

        if not self.downsample_type:

            for subj,trials in self.subject_trials.items():
                self.subject_trial_indices[subj] = []
                
                for resp,trial in trials:
                    self.subject_trial_indices[subj].append(len(self.design))
                    #self.design.append(trial[self.m])
                    self.design.append(trial)
                    self.Y.append(resp)


        elif self.downsample_type == 'group':
            
            positive_trials = []
            negative_trials = []
            
            for subj,trials in self.subject_trials.items():
                self.subject_trial_indices[subj] = []
                for [resp,trial] in trials:
                    if float(resp) > 0:
                        #positive_trials.append([subj,trial[self.m]])
                        positive_trials.append([subj,trial])
                    elif float(resp) < 0:
                        #negative_trials.append([subj,trial[self.m]])
                        negative_trials.append([subj,trial])
            
            
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
            
            
            for subj,trials in self.subject_trials.items():
                self.subject_trial_indices[subj] = []
                
                subject_positives = []
                subject_negatives = []
                
                for [resp,trial] in trials:
                    if float(resp) > 0:
                        #subject_positives.append(trial[self.m])
                        subject_positives.append(trial)
                    elif float(resp) < 0:
                        #subject_negatives.append(trial[self.m])
                        subject_negatives.append(trial)
            
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

        
    def instantiate_all(self, vars=None, nuke=False):
        if not vars == None:
            self._instantiate_vars(vars)
    
        self.create_reg_mask()
        
        data_found = False
        if not nuke:
            data_found = self.load_data_matrix()
        if nuke or not data_found:
            self.create_data_matrix()
    
        self.parse_resp_vecs()
        self.combine_data_vectors()
        self.generate_design_matrix()
        self.free_raw_data()
        
    
    def reinstantiate_design(self, vars=None):
        if not vars == None:
            self._instantiate_vars(vars)
            
        self.generate_design_matrix()
    
    


class RegRegPipe(object):
    
    def __init__(self, rrdata):
        super(RegRegPipe, self).__init__()
        self._instantiate_rrdata(rrdata)
        
        if not getattr(self,'crossvalidation_type',None):
            setattr(self,'crossvalidation_type','subject')
            
        
        self.coefs_name = 's:%s_r:%s_g:%s_l3:%s_coefs.npy' % (str(float(self.bound1)),
                                                           str(float(self.bound2)),
                                                           str(float(self.bound3)),
                                                           str(float(self.lambda3)))
        # results collectors:
        self.l1_norms = []
        self.l2_norms = []
        self.graphnet_norms = []
        self.accuracies = []

        np.random.seed(self.random_seed)
        random.seed(self.random_seed)
        
        
        
    def _instantiate_rrdata(self, rrdata):
        self.rrdata = rrdata
        self.vars = self.rrdata.vars
        
        for key, value in self.vars.items():
            setattr(self,key,value)
            
        self.design = self.rrdata.design
        self.Y = self.rrdata.Y
        self.subject_trial_indices = self.rrdata.subject_trial_indices
        self.m = self.rrdata.m
        self.mask_shape = self.rrdata.mask_shape
        self.raw_affine = self.rrdata.raw_affine
        self.raw_data_shape = self.rrdata.raw_data_shape




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
                for subject in train_set:
                    train_trials.extend(self.subject_trial_indices[subject])
                for subject in test_set:
                    test_trials.extend(self.subject_trial_indices[subject])
                    
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
        
        # adding a global intercept as the first column
        self.intercept = True
        self.design = np.array(self.design)

        self.X, self.image_selector, self.intercept_selector = \
            normalize_design(self.design, self.intercept, self.subject_trial_indices)

        if not crossvalidate:
            self.Y_signs = np.array(self.Y)
            self.Y_binary = (self.Y_signs + 1) / 2.
            
        else:

            train_design = self.X[train_trials]
            test_design = self.X[test_trials]
            
            self.X = rr.linear_transform(train_design)
            self.X_test = rr.linear_transform(test_design)
                
            tic = time.time()
            print 'normalization time: %0.1f' % (tic-toc)
            
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
        return rr.logistic_deviance.linear(self.X,successes=self.Y_binary)

    def quadratic_loss(self):
        return rr.quadratic.affine(self.X,-self.Y_signs,coef=0.5)

    def huber_loss(self):
        return rr.huber_loss.linear(self.X,delta=0.3,coef=0.5)
        
    @property
    def ridge_bound(self):
        p0 = self.image_selector.dual_shape
        pen = rr.l2norm(p0,bound=self.bound2)
        if self.intercept:
            return rr.separable(self.image_selector.primal_shape, [pen], [self.image_selector.index_obj])
        else:
            return pen

    @property
    def ridge_bound_smooth(self):
        p0 = self.image_selector.dual_shape
        pen = rr.l2norm(p0,bound=self.bound2)
        iq = rr.identity_quadratic(0.001,0,0,0)
        pens = pen.smoothed(iq)
        if self.intercept:
            p = rr.affine_smooth(pens, self.image_selector)
        else:
            p = pen
        return p

    @property
    def ridge(self):
        if self.lambda2 > 0:
            return rr.quadratic.linear(self.image_selector,coef=self.lambda2)
        else:
            return None
        
    @property
    def sparsity(self):
        p0 = self.image_selector.dual_shape
        if self.lambda1 > 0:
            pen = rr.l1norm(p0,lagrange=self.lambda1)
            if self.intercept:
                return rr.separable(self.image_selector.primal_shape, [pen], [self.image_selector.index_obj])
            return pen
        else:
            return None

    @property
    def sparsity_bound(self):
        p0 = self.image_selector.dual_shape
        pen = rr.l1norm(p0,bound=self.bound1)
        if self.intercept:
            return rr.separable(self.image_selector.primal_shape, [pen], [self.image_selector.index_obj])
        else:
            return pen

    @property
    def graphnet(self):
        l = rr.affine_composition(self.D, self.image_selector)
        if self.lambda3 > 0:
            return rr.quadratic.linear(l,coef=self.lambda3)
        else:
            return None

    @property
    def graphnet_bound(self):
        l = rr.affine_composition(self.D, self.image_selector)
        return rr.l2norm.linear(l,bound=self.bound3)

    @property
    def graphnet_bound_smooth(self):
        iq = rr.identity_quadratic(0.001,0,0,0)
        return self.graphnet_bound.smoothed(iq)

    @property
    def penalty(self):
        ps = [getattr(self, p) for p in self.penalties]
        return [p for p in ps if p is not None]

    def problem(self):
        loss = {'logistic': self.logistic_loss(),
                'quadratic': self.quadratic_loss()# ,
#                 'huber': self.huber_loss()
                }[self.loss]

        use_container = False

        def issmooth(p):
            if isinstance(p, rr.smooth_atom) or isinstance(p, rr.smooth_composite):
                return True
            return False

        if not use_container:
            smooth_ps = [p for p in self.penalty if issmooth(p)]
            nonsmooth_ps = [p for p in self.penalty if not issmooth(p)]
            full_loss = theloss(*([loss] + smooth_ps))

            if len(nonsmooth_ps) > 1:
                raise ValueError('can only handle single nonsmooth right now')
            return rr.simple_problem(full_loss, nonsmooth_ps[0])
        else:
            p = rr.container(loss, *self.penalty)
            return p

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

        image_solution = self.image_selector.linear_map(self.solution)
        if self.intercept_selector is not None:
            intercept_solution = self.intercept_selector.linear_map(self.solution)
        else:
            intercept_solution = None

        l1_norm = np.fabs(image_solution).sum()
        l2_norm = np.linalg.norm(image_solution)
        graphnet_norm = np.linalg.norm(self.D * image_solution)
        
        pprint('l1 norm: %f' % l1_norm)
        pprint('l2 norm: %f' % l2_norm)
        pprint('graphnet norm: %f' % graphnet_norm)
        if intercept_solution is not None:
            #pprint('intercept: %f' % intercept_solution)
            pprint(intercept_solution)
        

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
                self.solution_shaped[np.where(self.m)] = image_solution
            
            else:
                self.solution_shaped = image_solution.reshape(self.raw_data_shape[0],
                                                              self.raw_data_shape[1],
                                                              self.raw_data_shape[2],
                                                              self.reg_prediction_tr_len)
        
        
        
    
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
        
        
        if self.warm_start:
            coefs_found = self.load_coefs()
        
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


def normalize_design(X, intercept, subject_trial_indices=None):
    
    Xn = rr.normalize(X, center=True, scale=True, inplace=True)
    which0 = Xn.col_stds == 0
    X = Xn.M
    X[:,which0] = 0
    del(Xn); gc.collect()

    if intercept:
        if subject_trial_indices is None: # a global intercept
            X = np.hstack([np.ones((X.shape[0],1)), X])
            image_selector = rr.selector(slice(1, None), X.shape[1:])
            intercept_selector = rr.selector(slice(0, 1), X.shape[1:])
        else:
            new_cols = np.zeros((X.shape[0], len(subject_trial_indices)))
            print 'INTERCEPT INFO:'
            print 'new cols shape: %s' % str(np.shape(new_cols))
            print 'X shape: %s' % str(np.shape(X))
            indsum = 0
            for colidx, (subj, indices) in enumerate(subject_trial_indices.items()):
                #print 'Col: %s' % str(colidx)
                new_col = np.zeros(X.shape[0])
                new_col[indices] = 1
                indsum = indsum + sum(new_col)
                #print 'col sum: %s' % str(sum(new_col))
                #print 'subject: %s' % str(subj)
                #print 'subj ind len: %s' % str(len(indices))
                new_cols[:,colidx] = new_col
            print 
            X = np.hstack([new_cols, X])
            print 'intercepts sum: %s' % str(indsum)
            print 'new X shape: %s' % str(np.shape(X))
            image_selector = rr.selector(slice(new_cols.shape[1], None), X.shape[1:])
            intercept_selector = rr.selector(slice(0, new_cols.shape[1]), X.shape[1:])
    else:
        image_selector = rr.identity(X.shape[1:])
        intercept_selector = None

    return rr.linear_transform(X), image_selector, intercept_selector

        


class theloss(rr.smooth_atom): # a hack way to combine smooth functions

    def __init__(self, *smooth_atoms):
        self.smooth_atoms = smooth_atoms
        rr.smooth_atom.__init__(self,
                                smooth_atoms[0].primal_shape)

    def smooth_objective(self, x, mode='both', check_feasibility=False):
        f, g = 0, 0
        for atom in self.smooth_atoms:
            if mode == 'grad':
                g += atom.smooth_objective(x, mode='grad', check_feasibility=check_feasibility)
            elif mode == 'func':
                f += atom.smooth_objective(x, mode='func', check_feasibility=check_feasibility)
            elif mode == 'both':
                fc, gc = atom.smooth_objective(x, mode='both', check_feasibility=check_feasibility)
                f += fc
                g += gc
        return {'both':(f,g), 'func':f, 'grad':g}[mode]
    
    
    
    
    
    
    
    
    
    
    
