import sys
import os
import glob
from types import *


if sys.version_info[0] >= 3:
    raise Exception("The legacy objdictgen must be run with py2")

if len(sys.argv) < 2:
    raise Exception("Missing directory to legacy objdictgen")

sys.path.insert(0, os.path.abspath(sys.argv[1]))

from nodemanager import *

def convert(fname):
    base = fname.replace('.od', '')

    manager = NodeManager()
    print("Reading %s" % fname)
    result = manager.OpenFileInCurrent(base + '.od')
    if isinstance(result, (StringType, UnicodeType)):
        print(result)
        sys.exit(1)

    print("    Writing c")
    result = manager.ExportCurrentToCFile(base + '.c')
    if isinstance(result, (UnicodeType, StringType)):
        print(result)
        sys.exit(1)

    print("    Writing eds")
    result = manager.ExportCurrentToEDSFile(base + '.eds')
    if isinstance(result, (UnicodeType, StringType)):
        print(result)
        sys.exit(1)

os.chdir(os.path.abspath(os.path.split(__file__)[0]))
for fname in glob.glob('*.od'):
    convert(fname)
for fname in glob.glob(os.path.join('extra', '*.od')):
    convert(fname)
