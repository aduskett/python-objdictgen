import os
import glob

from objdictgen.nodemanager import NodeManager

here = os.path.dirname(os.path.abspath(__file__))

def convert(fname):
    base = fname.replace('.od', '')

    manager = NodeManager()
    print("Reading %s" % fname)
    manager.OpenFileInCurrent(base + '.od')

    print("    Writing json")
    manager.ExportCurrentToJsonFile(base + '.json')

os.chdir(here)

# for fname in glob.glob('*.od'):
#     convert(fname)
for fname in glob.glob(os.path.join('legacy', '*.od')):
    convert(fname)
