import os
import glob

from objdictgen.nodemanager import NodeManager

def convert(fname):
    base = fname.replace('.od', '')

    manager = NodeManager()
    print("Reading %s" % fname)
    manager.OpenFileInCurrent(base + '.od')
    print("    Writing json")
    manager.ExportCurrentToJsonFile(base + '.json')

os.chdir(os.path.abspath(os.path.split(__file__)[0]))
for fname in glob.glob('*.od'):
    convert(fname)
for fname in glob.glob(os.path.join('extra', '*.od')):
    convert(fname)
