#!/usr/bin/env python

import os

def vecmaker(filename):
    file = open(filename,'wb')
    counter = 0
    for i in range(560):
        if counter == 0:
            file.write('1\n')
        else:
            file.write('0\n')
        if counter == 6:
            counter = 0
        else:
            counter = counter+1
    file.close()


if __name__ == '__main__':
    vecmaker('trialonsets.1D')