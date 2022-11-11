import sys
import os
import argparse
import shutil
# import glob

if sys.version_info[0] >= 3:
    raise Exception("The legacy objdictgen must be run with py2")

parser = argparse.ArgumentParser()
parser.add_argument("objdictgen_dir", help="Directory to legacy objdictgen sources")
parser.add_argument("od_dir", help="Directory to ODs")
parser.add_argument("out_dir", nargs="?", help="Output directory. Use od_dir if omitted.")
opts = parser.parse_args()

sys.path.insert(0, os.path.abspath(opts.objdictgen_dir))
from nodemanager import *


if opts.out_dir:
    out_dir = os.path.abspath(opts.out_dir)
else:
    out_dir = os.path.abspath(opts.od_dir)

if not os.path.exists(out_dir):
    os.mkdir(out_dir)


def convert(path):
    ipath, fname = os.path.split(path)
    #opath = os.path.join(ipath, 'out_dir')
    opath = ipath
    base = fname.replace('.od', '')

    manager = NodeManager()
    print("Reading %s" % fname)
    result = manager.OpenFileInCurrent(os.path.join(ipath, base + '.od'))
    if isinstance(result, (StringType, UnicodeType)):
        print(result)
        sys.exit(1)

    print("    Writing c")
    result = manager.ExportCurrentToCFile(os.path.join(opath, base + '.c'))
    if isinstance(result, (UnicodeType, StringType)):
        print(result)
        sys.exit(1)

    print("    Writing eds")
    result = manager.ExportCurrentToEDSFile(os.path.join(opath, base + '.eds'))
    if isinstance(result, (UnicodeType, StringType)):
        print(result)
        sys.exit(1)


for root, dirs, files in os.walk(opts.od_dir):
    for fname in files:
        if not fname.endswith('.od'):
            continue

        src = os.path.abspath(os.path.join(root, fname))
        dst = os.path.join(out_dir, fname)
        if src != dst:
            shutil.copyfile(src, dst)

        try:
            convert(dst)
        except Exception as err:
            print("FAILED: %s" %(err,))
