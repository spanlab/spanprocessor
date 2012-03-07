#!/usr/bin/env python


import os
import glob
import sys
import pkgutil
import re


# import functions/classes from utilities folder:
from processor.utilities.shell_command import shell_command
from processor.utilities.parse_dirs import parse_dirs
from processor.utilities.general_cleaner import general_cleaner
from processor.utilities import DirectoryCleaner

# load up primary classes:
from processor.SorcerersApprentice import (SorcerersApprentice, Worker)

from processor.Pipe import Pipe

from processor.afni.AfniProcess import AfniProcess

from processor.afni.AfniBase import *

from processor.afni.PyAfni import *

