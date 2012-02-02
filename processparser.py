#!/usr/bin/env python

import os
import string
from mono_utility import parse_dirs



def process_parser(filename,designation,plimit=2):
    file = open(filename,'rb')
    lines = file.readlines()
    file.close()
    pfiles = []
    ivalues = []
    svalues = []
    grecons = []
    output = 'pop'+designation
    for line in lines:
        line = line.strip('\t\n')
        if line.startswith('grecons11') and len(pfiles) < plimit:
            pfiles.append(line[line.index('P'):line.index('.')])
            grecons.append('grecons11')
        if line.startswith('grecons ') and len(pfiles) < plimit:
            pfiles.append(line[line.index('P'):line.index('.')])
            grecons.append('grecons')
        if line.startswith('grecons12') and len(pfiles) < plimit:
            pfiles.append(line[line.index('P'):line.index('.')])
            grecons.append('grecons12')
        if line.startswith('to3d'):
            ivalues.append(line[line.index('I')-4:line.index('I')])
            if line.find('S ') != -1:
		svalues.append(line[line.index('S ')-4:line.index('S ')])
	    elif line.find('S-') != -1:
		print "incorrect"
		svalues.append(line[line.index('S-')-4:line.index('S-')])
    #print grecons
    return [pfiles,ivalues,svalues,output,grecons[0]]


def masterwriter(master):
    allp1 = []
    allp2 = []
    alli1 = []
    alli2 = []
    alls1 = []
    alls2 = []
    grecons = []
    allout = []
    allsub = []
    for set in master:
        allp1.append(set[0][0])
        allp2.append(set[0][1])
        alli1.append(set[1][0])
        alli2.append(set[1][1])
        alls1.append(set[2][0])
        alls2.append(set[2][1])
        allout.append(set[3])
        allsub.append(set[4])
	grecons.append(set[5])
    file = open('processinfo.txt','wb')
    file.write('Pfiles1:\n')
    file.write(' '.join(allp1)+'\n\n')
    file.write('Pfiles2:\n')
    file.write(' '.join(allp2)+'\n\n')
    file.write('Grecons:\n')
    file.write(' '.join(grecons)+'\n\n')
    file.write('Ivalues1:\n')
    file.write(' '.join(alli1)+'\n\n')
    file.write('Ivalues2:\n')
    file.write(' '.join(alli2)+'\n\n')
    file.write('Svalues1:\n')
    file.write(' '.join(alls1)+'\n\n')
    file.write('Svalues2:\n')
    file.write(' '.join(alls2)+'\n\n')
    file.write('Outputs:\n')
    file.write(' '.join(allout)+'\n\n')
    file.write('Subjects:\n')
    file.write(' '.join(allsub))
    
    

if __name__ == '__main__':
    master = []
    os.chdir('../')
    dirs = parse_dirs(exclude=['analysis','binnedvectors','exclude','fulltcs',
                               'inddiff','insula','insulapd','insulapref',
                               'masktemp','merge','mpfc','mpfcpd','mpfcpref',
                               'nacc','naccpref','naccpd','racing','reg_output',
                               'scripts','spanprocessor','testSub','timecourses',
                               'ttests','vectors','allSubTC'])
    for subject in dirs:
        print subject
        os.chdir(subject)
        single = True
        if os.path.exists('process12'):
            [pfiles,ivalues,svalues,output,grecons] = process_parser('process12','12')
            #print pfiles
            #print ivalues
            #print svalues
            #print output
            #print grecons
            master.append([pfiles,ivalues,svalues,output,subject.strip('/'),grecons])
            single = False
        if os.path.exists('process34'):
            [pfiles,ivalues,svalues,output,grecons] = process_parser('process34','34')
            master.append([pfiles,ivalues,svalues,output,subject.strip('/'),grecons])
            single = False
            #print pfiles
            #print ivalues
            #print svalues
            #print output
            #print grecons
        if single and os.path.exists('process'):
            [pfiles,ivalues,svalues,output,grecons] = process_parser('process','12')
            master.append([pfiles,ivalues,svalues,output,subject.strip('/'),grecons])
            #print pfiles
            #print ivalues
            #print svalues
            #print output
            #print grecons
	elif single and os.path.exists('process1234'):
	    [pfiles,ivalues,svalues,output,grecons] = process_parser('process1234','12',plimit=4)
	    master.append([pfiles[0:2],ivalues[0:2],svalues[0:2],output,subject.strip('/'),grecons])
	    master.append([pfiles[2:4],ivalues[2:4],svalues[2:4],'pop34',subject.strip('/'),grecons])
	    #print pfiles
	    #print ivalues
	    #print svalues
	    #print output
	    #print grecons
        os.chdir('../')
    os.chdir('spanprocessor')
    masterwriter(master)
