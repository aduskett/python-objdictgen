import os
import glob
import sys
import logging

from objdictgen.nodemanager import NodeManager

# Initalize the python logger to simply output to stdout
log = logging.getLogger()
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))

here = os.path.dirname(os.path.abspath(__file__))

def convert(fname):
    base = fname.replace('.od', '')

    manager = NodeManager()
    print("Reading %s" % fname)
    manager.OpenFileInCurrent(base + '.od')

    manager.CurrentNode.Validate(fix=True)

    print("    Writing json")
    manager.ExportCurrentToJsonFile(base + '.json', sort=True)

os.chdir(here)

# for fname in glob.glob('*.od'):
#     convert(fname)
for fname in glob.glob(os.path.join('extra', '*.od')):
    convert(fname)
