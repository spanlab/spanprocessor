#!/usr/bin/env python


import os
import sys
import shutil
import glob
import re
import pkgutil
from pprint import pprint

from utilities.parse_dirs import parse_dirs
from utilities.general_cleaner import general_cleaner
from utilities.shell_command import shell_command