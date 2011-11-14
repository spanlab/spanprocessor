#!/usr/bin/env python

import glob
import sys
import os
import shutil
import string
from mono_utility import parse_dirs

'''
DIRECTORYCLEANER
11.03.11        Kiefer Katovich

DirectoryCleaner is a lil' class that helps you clean up old files from data
directories. It allows moving of filetypes and deletion of filetypes.

When you initialize the class, you can specify a specific_directories keyword
argument that should be a list of directory names that you specifically/only
want to clean from.

The class has only 2 functions that you should be using:

DirectoryCleaner.move and DirectoryCleaner.remove

Each takes, as arguments, strings denoting the suffix of the files that you
want to remove or move.

Examples:

DirectoryCleaner.remove('txt','csv','jpeg')
# Removes .txt files, .csv files, and .jpeg files from specified directories

DirectoryCleaner.move('HEAD','BRIK','1D')
# moves HEAD and BRIK files into ./old_afni, moves 1D files into ./old_1d within
subject directories

'''


class DirectoryCleaner:
    def __init__(self,specific_directories=False,exclude_dirs=False,run_from_scripts_dir=True):
        if run_from_scripts_dir: os.chdir('../')
        if not specific_directories:
            if not exclude_dirs:
                self.directories = parse_dirs()
            else:
                self.directories = parse_dirs(exclude=exclude_dirs)
        else:
            if not exclude_dirs:
                self.directories = parse_dirs(prefixes=specific_directories)
            else:
                self.directories = parse_dirs(prefixes=specific_directories,exclude=exclude_dirs)
        self.types = []
        self.files = []
        print self.directories
    def __walk_directories(self,function):
        for dir in self.directories:
            os.chdir(dir)
            self.files = glob.glob('./*')
            function()
            os.chdir('../')
        self.files = []
    def __action_flag(self,action):
        if action == 'rm':
            for file in self.files:
                for flag in self.types:
                    if not flag.startswith('.'):
                        flag = '.'+flag
                    if file.endswith(flag): os.remove(file)
        elif action == 'mv':
            for flag in self.types:
                if not flag.startswith('.'):
                    flag = '.'+flag
                if not flag == '.HEAD' or not flag == '.BRIK':
                    dir_name = './old_'+flag.strip('.')
                    if not os.path.exists(dir_name):
                        os.mkdir(dir_name)
                    for file in self.files:
                        if file.endswith(flag): shutil.move(file,dir_name)
                else:
                    dir_name = './old_afni'
                    if not os.path.exists(dir_name):
                        os.mkdir(dir_name)
                    for file in self.files:
                            if file.endswith(flag): shutil.move(file,dir_name)   
    def remove(self,*args):
        print os.getcwd()
        if args:
            self.types = args
            print self.types
        if not self.files:
            self.__walk_directories(self.remove)
        else:
            self.__action_flag('rm')
    def move(self,*args):
        print os.getcwd()
        if args:
            self.types = args
            print self.types
        if not self.files:
            self.__walk_directories(self.move)
        else:
            self.__action_flag('mv')









