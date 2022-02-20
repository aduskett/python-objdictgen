from pprint import pprint
import shutil
import re
import os
import sys
import pytest
from objdictgen.nodemanager import NodeManager


BASE = os.path.join(os.path.split(__file__)[0], '..')


def test_load_compare(odfile, fn):
    # Load the OD
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    # Load the OD a second time and compare it
    m2 = NodeManager()
    m2.OpenFileInCurrent(odfile + '.od')

    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__


def test_odexport(odfile, fn):
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    # Save the OD
    m1.SaveCurrentInFile(odfile + '.od2')

    # Modify the od files to remove unique elements
    RE_ID = re.compile(r'(id|module)="\w+"')
    with open(odfile + '.od', 'r') as fi:
        with open(odfile + '.od1', 'w') as fo:
            for line in fi:
                fo.write(RE_ID.sub('', line))
    shutil.move(odfile + '.od2', odfile + '.od2_t')
    with open(odfile + '.od2_t', 'r') as fi:
        with open(odfile + '.od2', 'w') as fo:
            for line in fi:
                fo.write(RE_ID.sub('', line))
    os.remove(odfile + '.od2_t')

    # Load the saved OD
    m2 = NodeManager()
    m2.OpenFileInCurrent(odfile + '.od2')

    # Compare the OD master and the OD2 objects
    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__

    # Compare the files - The py3 ones are by guarantee different, as the str handling is different
    if sys.version_info[0] < 3:
        assert not list(fn.diff(odfile + '.od1', odfile + '.od2', n=0))


def test_odcompare23(odfile, fn):
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')
    m1.SaveCurrentInFile(odfile + '.od2')

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od2')

    oposite = odfile.replace(fn.DUT, fn.OPOSITE)
    if not os.path.exists(oposite + '.od2'):
        raise pytest.skip("Missing .od2 files from '%s'" %(oposite + '.od2'))
    m2 = NodeManager()
    m2.OpenFileInCurrent(oposite + '.od2')

    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__


def test_cexport(odfile, fn):
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToCFile(odfile + '.c')

    assert not list(fn.diff_ref(odfile + '.c'))
    assert not list(fn.diff_ref(odfile + '.h'))
    assert not list(fn.diff_ref(odfile + '_objectdefines.h'))


def test_edsexport(odfile, fn):
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToEDSFile(odfile + '.eds')

    def predicate(line):
        for m in ('CreationDate', 'CreationTime', 'ModificationDate', 'ModificationTime'):
            if m in line:
                return False
        return True

    assert not list(fn.diff_ref(odfile + '.eds', predicate=predicate))


def test_edsimport(odfile, fn):
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToEDSFile(odfile + '.eds')

    m2 = NodeManager()
    m2.ImportCurrentFromEDSFile(odfile + '.eds')

    # EDS isn't complete enough to compare with an OD-loaded file
    # assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__
