#!/usr/bin/env python


'''
PARSE_DIRS
11.01.11     Kiefer Katovich

Parse the folders in the current directories for only the ones you want.
Takes two keyworded arguments: prefixes and shave_front. prefixes defaults to an
empty list, and shave_front defaults to True. If you specify prefixes, it will
only return folders that begin with that prefix (ignoring the ./). If
shave_front is set to False, the ./ is included in the string filenames,
otherwise it is not.

Examples:

Lets say the directory is:
.
..
hey.txt
folder1/
folder2/
aa01/
bb02/

parsed = parse_dirs()
parsed = ['folder1/','folder2/','aa01/','bb02/']

parsed = parse_dirs(prefixes=['aa','bb'],shave_front=False)
parsed = ['./aa01/','./bb02/']

Could be better, but good enough fo' now.

'''

def parse_dirs(prefixes=[],exclude=[],shave_front=True):
    directory_contents = glob.glob('./*/')
    parsed = []
    if prefixes:
        for file in directory_contents:
            for prefix in prefixes:
                if (file.strip('./')).startswith(prefix):
                    if exclude:
                        flag = 0
                        for exclusion in exclude:
                            if (file.strip('./').startswith(exclusion)):
                                flag = 1
                        if not flag:
                            if shave_front:
                                parsed.append(file[2:])
                            else:
                                parsed.append(file)
                    else:
                        if shave_front:
                            parsed.append(file[2:])
                        else:
                            parsed.append(file)
    else:
        for file in directory_contents:
            if exclude:
                flag = 0
                for exclusion in exclude:
                    if (file.strip('./').startswith(exclusion)):
                        flag = 1
                if not flag:
                    if shave_front:
                        if len(file) > 2: parsed.append(file[2:])
                    else:
                        if len(file) > 2: parsed.append(file)
            else:
                if shave_front:
                    if len(file) > 2: parsed.append(file[2:])
                else:
                    if len(file) > 2: parsed.append(file)    
    return parsed


