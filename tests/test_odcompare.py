import shutil
import re
import os
import sys
import pytest
from objdictgen.nodemanager import NodeManager


@pytest.mark.parametrize("suffix", ['.od', '.json', '.eds'])
def test_load_compare(odfile, suffix, fn):
    # Load the OD
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + suffix)

    # Load the OD a second time and compare it
    m2 = NodeManager()
    m2.OpenFileInCurrent(odfile + suffix)

    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__


def test_odexport(odfile, fn):
    base, od = os.path.split(odfile)

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    # Save the OD
    m1.ExportCurrentToODFile(od + '.od')

    # Modify the od files to remove unique elements
    RE_ID = re.compile(r'(id|module)="\w+"')
    with open(odfile + '.od', 'r') as fi:
        with open(od + '.od.in', 'w') as fo:
            for line in fi:
                fo.write(RE_ID.sub('', line))
    shutil.move(od + '.od', od + '.tmp')
    with open(od + '.tmp', 'r') as fi:
        with open(od + '.od', 'w') as fo:
            for line in fi:
                fo.write(RE_ID.sub('', line))
    os.remove(od + '.tmp')

    # Load the saved OD
    m2 = NodeManager()
    m2.ImportCurrentFromODFile(od + '.od')

    # Compare the OD master and the OD2 objects
    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__

    # Compare the files - The py3 ones are by guarantee different, as the str handling is different
    if sys.version_info[0] < 3:
        assert fn.diff(od + '.od.in', od + '.od', n=0)


def xtest_odcompare23(odfile, fn):
    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')
    m1.ExportCurrentToODFile(odfile + '.od2')

    m1 = NodeManager()
    m1.ImportCurrentFromODFile(odfile + '.od2')

    oposite = odfile.replace(fn.DUT, fn.OPOSITE)
    if not os.path.exists(oposite + '.od2'):
        raise pytest.skip("Missing .od2 files from '%s'" %(oposite + '.od2'))

    m2 = NodeManager()
    m2.ImportCurrentFromODFile(oposite + '.od2')

    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__


def test_jsonexport(odfile, fn):
    base, od = os.path.split(odfile)

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToJsonFile(od + '.json')

    m2 = NodeManager()
    m2.OpenFileInCurrent(odfile + '.od')

    # To verify that the export doesn't clobber the object
    assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__


def test_cexport(odfile, fn):
    base, od = os.path.split(odfile)

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToCFile(od + '.c')

    assert fn.diff(odfile + '.c', od + '.c', n=0)
    assert fn.diff(odfile + '.h', od + '.h', n=0)
    assert fn.diff(odfile + '_objectdefines.h', od + '_objectdefines.h', n=0)


def test_edsexport(odfile, fn):
    base, od = os.path.split(odfile)

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToEDSFile(od + '.eds')

    def predicate(line):
        for m in ('CreationDate', 'CreationTime', 'ModificationDate', 'ModificationTime'):
            if m in line:
                return False
        return True

    assert fn.diff(odfile + '.eds', od + '.eds', predicate=predicate)


def test_edsimport(odfile, fn):
    base, od = os.path.split(odfile)

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToEDSFile(od + '.eds')

    m2 = NodeManager()
    m2.ImportCurrentFromEDSFile(od + '.eds')

    # EDS isn't complete enough to compare with an OD-loaded file
    # assert m1.CurrentNode.__dict__ == m2.CurrentNode.__dict__


def dictify(d):
    if isinstance(d, dict):
        return {
            k: dictify(v)
            for k, v in d.items()
        }
    elif isinstance(d, list):
        return [
            dictify(v)
            for v in d
        ]
    return d


def test_jsonimport(odfile, fn):
    base, od = os.path.split(odfile)

    m1 = NodeManager()
    m1.OpenFileInCurrent(odfile + '.od')

    m1.ExportCurrentToJsonFile(od + '.json')

    m2 = NodeManager()
    m2.ImportCurrentFromJsonFile(od + '.json')

    cn1 = dictify(m1.CurrentNode.__dict__)
    cn2 = dictify(m2.CurrentNode.__dict__)

    assert cn1 == cn2
