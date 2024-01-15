import copy
import shutil
import re
import os
import sys
from collections import OrderedDict
import pytest

from objdictgen import Node

if sys.version_info[0] >= 3:
    ODict = dict
else:
    ODict = OrderedDict


def shave_dict(a, b):
    if isinstance(a, (ODict, dict)) and isinstance(b, (ODict, dict)):
        for k in set(a.keys()) | set(b.keys()):
            if k in a and k in b:
                a[k], b[k] = shave_dict(a[k], b[k])
            if k in a and k in b and a[k] == b[k]:
                del a[k]
                del b[k]
    return a, b


def shave_equal(a, b, ignore=None):
    a = copy.deepcopy(a.__dict__)
    b = copy.deepcopy(b.__dict__)

    for n in ignore or []:
        a.pop(n, None)
        b.pop(n, None)

    return shave_dict(a, b)


# TIPS:
#
# Printing of diffs:
#   # from objdictgen.__main__ import print_diffs
#   # from objdictgen import jsonod
#   # diffs = jsonod.diff_nodes(m0, m1, as_dict=False, validate=True)
#   # print_diffs(diffs)
#
# Saving for debug
#    # m1.SaveCurrentInFile('<filepath>/_tmp.err.json', sort=True, internal=True, validate=False)


# def dictify(d):
#     if isinstance(d, dict):
#         return {
#             k: dictify(v)
#             for k, v in d.items()
#         }
#     elif isinstance(d, list):
#         return [
#             dictify(v)
#             for v in d
#         ]
#     return d


# def del_IndexOrder(obj):
#     if hasattr(obj, 'IndexOrder'):
#         delattr(obj, 'IndexOrder')


@pytest.mark.parametrize("suffix", [".od", ".json", ".eds"])
def test_load_compare(odfile, suffix):
    """Tests that the file can be loaded twice without different.
    L(od) == L(od)
    """
    odfile_path = f"{odfile}{suffix}"
    if not os.path.exists(odfile_path):
        pytest.skip("File not found")

    # Load the OD
    m1 = Node.LoadFile(odfile_path)
    m2 = Node.LoadFile(odfile_path)

    assert m1.__dict__ == m2.__dict__


def test_odexport(wd, odfile, fn):
    """Test that the od file can be exported to od and that the loaded file
    is equal to the first.
    L(od) -> S(od2), od == L(od2)
    """
    od = odfile.name
    od_generated = f"{od}.od"
    od_orig = f"{od}.od.orig"
    od_path = f"{odfile}.od"
    od_temp = f"{od}.tmp"
    m0 = Node.LoadFile(od_path)
    m1 = Node.LoadFile(od_path)

    # Save the OD
    m1.DumpFile(od_generated, filetype="od")

    # Assert that the object is unmodified by the export
    assert m0.__dict__ == m1.__dict__

    # Modify the od files to remove unique elements
    #  .od.orig  is the original .od file
    #  .od       is the generated .od file
    RE_ID = re.compile(r'(id|module)="\w+"')
    with open(od_path, "r") as fi:
        with open(od_orig, "w") as fo:
            for line in fi:
                fo.write(RE_ID.sub("", line))
    shutil.move(od_generated, od_temp)
    with open(od_temp, "r") as fi:
        with open(od_generated, "w") as fo:
            for line in fi:
                fo.write(RE_ID.sub("", line))
    os.remove(od_temp)

    # Load the saved OD
    m2 = Node.LoadFile(od_generated)

    # Compare the OD master and the OD2 objects
    assert m1.__dict__ == m2.__dict__

    # Compare the files - The py3 ones are by guarantee different, as the str handling is different
    if sys.version_info[0] < 3:
        assert fn.diff(od_orig, od + ".od", n=0)


def test_jsonexport(wd, odfile):
    """Test that the file can be exported to json and that the loaded file
    is equal to the first.
    L(od) -> fix -> S(json), L(od) == od
    """
    od = odfile.name
    od_json = f"{od}.json"
    od_path = f"{odfile}.od"
    m0 = Node.LoadFile(od_path)
    m1 = Node.LoadFile(od_path)

    # Need this to fix any incorrect ODs which cause import error
    m0.Validate(fix=True)
    m1.Validate(fix=True)

    m1.DumpFile(od_json, filetype="json")

    # Assert that the object is unmodified by the export
    assert m0.__dict__ == m1.__dict__

    m2 = Node.LoadFile(od_path)

    # To verify that the export doesn't clobber the object
    equal = m1.__dict__ == m2.__dict__

    # If this isn't equal, then it could be the fix option above, so let's attempt
    # to modify m2 with the same change
    if not equal:
        m2.Validate(fix=True)

    assert m1.__dict__ == m2.__dict__


def test_cexport(wd, odfile, fn):
    """Test that the file can be exported to c and that the loaded file
    is equal to the stored template (if present).
    L(od) -> S(c), diff(c)
    """
    cfile_type = {"cfile_type": 0}
    od = odfile.name

    m0 = Node.LoadFile(f"{odfile}.od")
    m1 = Node.LoadFile(f"{odfile}.od")
    m1.DumpFile(f"{od}.c", filetype="c", **cfile_type)

    # Assert that the object is unmodified by the export
    assert m0.__dict__ == m1.__dict__

    # FIXME: If files doesn't exist, this leaves this test half-done. Better way?
    if os.path.exists(f"{odfile}.c"):
        assert fn.diff(f"{odfile}.c", f"{od}.c", n=0)
        assert fn.diff(f"{odfile}.h", f"{od}.h", n=0)
        assert fn.diff(f"{odfile}_objectdefines.h", f"{od}_objectdefines.h", n=0)


def test_edsexport(wd, odfile, fn):
    """Test that the file can be exported to eds and that the loaded file
    is equal to the stored template (if present)
    L(od) -> S(eds), diff(eds)
    """
    od = odfile.name

    if od == "null":
        pytest.skip("Won't work for null")

    m0 = Node.LoadFile(f"{odfile}.od")
    m1 = Node.LoadFile(f"{odfile}.od")

    m1.DumpFile(f"{od}.eds", filetype="eds")

    # Assert that the object is unmodified by the export
    assert m0.__dict__ == m1.__dict__

    def predicate(line):
        for m in (
            "CreationDate",
            "CreationTime",
            "ModificationDate",
            "ModificationTime",
        ):
            if m in line:
                return False
        return True

    # FIXME: If file doesn't exist, this leaves this test half-done. Better way?
    if os.path.exists(f"{odfile}.eds"):
        assert fn.diff(f"{odfile}.eds", f"{od}.eds", predicate=predicate)


def test_edsimport(wd, odfile):
    """Test that EDS files can be exported and imported again.
    L(od) -> S(eds), L(eds)
    """
    od = odfile.name

    if od == "null":
        pytest.skip("Won't work for null")

    m1 = Node.LoadFile(f"{odfile}.od")

    # Need this to fix any incorrect ODs which cause EDS import error
    # m1.Validate(correct=True)

    m1.DumpFile(f"{od}.eds", filetype="eds")


def test_jsonimport(wd, odfile):
    """Test that JSON files can be exported and read back. It will be
    compared with orginal contents.
    L(od) -> fix -> S(json), od == L(json)
    """
    od = odfile.name

    m1 = Node.LoadFile(f"{odfile}.od")

    # Need this to fix any incorrect ODs which cause import error
    m1.Validate(fix=True)

    m1.DumpFile(f"{od}.json", filetype="json")
    m1.DumpFile(f"{od}.json2", filetype="json", compact=True)

    m2 = Node.LoadFile(f"{od}.json")

    a, b = shave_equal(m1, m2, ignore=("IndexOrder",))
    assert a == b

    m3 = Node.LoadFile(f"{od}.json2")

    a, b = shave_equal(m1, m3, ignore=("IndexOrder",))
    assert a == b


def test_od_json_compare(odfile):
    """Test reading the od and compare it with the corresponding json file
    L(od) == L(json)
    """

    if not os.path.exists(f"{odfile}.json"):
        raise pytest.skip(f"No .json file for {odfile}.od")

    m1 = Node.LoadFile(f"{odfile}.od")
    m2 = Node.LoadFile(f"{odfile}.json")

    # To verify that the export doesn't clobber the object
    a, b = shave_equal(m1, m2, ignore=("IndexOrder",))
    equal = a == b

    # If this isn't equal, then it could be the fix option above, so let's attempt
    # to modify m1 with the fix
    if not equal:
        m1.Validate(fix=True)

    a, b = shave_equal(m1, m2, ignore=("IndexOrder",))
    assert a == b


PROFILE_ODS = [
    "test-profile",
    "test-profile-use",
    "master-ds302",
    "master-ds401",
    "master-ds302-ds401",
    "legacy-test-profile",
    "legacy-test-profile-use",
    "legacy-master-ds302",
    "legacy-master-ds401",
    "legacy-master-ds302-ds401",
    "legacy-slave-ds302",
    "legacy-slave-emcy",
    "legacy-slave-heartbeat",
    "legacy-slave-nodeguarding",
    "legacy-slave-sync",
]


@pytest.mark.parametrize("oddut", PROFILE_ODS)
@pytest.mark.parametrize("suffix", ["od", "json"])
def test_save_wo_profile(oddir, oddut, suffix, wd):
    """Test that saving a od that contains a profile creates identical
    results as the original. This test has no access to the profile dir
    """

    fa = str(os.path.join(oddir, oddut))

    m1 = Node.LoadFile(f"{fa}.od")
    m1.DumpFile(f"{oddut}.{suffix}", filetype=suffix)

    m2 = Node.LoadFile(f"{oddut}.{suffix}")

    a, b = shave_equal(m1, m2, ignore=("IndexOrder",))
    assert a == b


@pytest.mark.parametrize("oddut", PROFILE_ODS)
@pytest.mark.parametrize("suffix", ["od", "json"])
def test_save_with_profile(oddir, oddut, suffix, wd, profile):
    """Test that saving a od that contains a profile creates identical
    results as the original. This test have access to the profile dir
    """

    fa = str(os.path.join(oddir, oddut))

    m1 = Node.LoadFile(f"{fa}.od")
    m1.DumpFile(f"{oddut}.{suffix}", filetype=suffix)

    m2 = Node.LoadFile(f"{oddut}.{suffix}")

    a, b = shave_equal(m1, m2, ignore=("IndexOrder",))
    assert a == b


@pytest.mark.parametrize(
    "equivs",
    [
        ("minimal.od", "legacy-minimal.od"),
        ("minimal.json", "legacy-minimal.od"),
        ("master.od", "legacy-master.od"),
        ("master.json", "legacy-master.od"),
        ("slave.od", "legacy-slave.od"),
        ("slave.json", "legacy-slave.od"),
        ("alltypes.od", "legacy-alltypes.od"),
        ("alltypes.json", "legacy-alltypes.od"),
        ("test-profile.od", "legacy-test-profile.od"),
        ("test-profile-use.od", "legacy-test-profile-use.od"),
        ("master-ds302.od", "legacy-master-ds302.od"),
        ("master-ds401.od", "legacy-master-ds401.od"),
        ("master-ds302-ds401.od", "legacy-master-ds302-ds401.od"),
    ],
)
def test_legacy_compare(oddir, equivs):
    """Test reading the od and compare it with the corresponding json file"""
    a, b = equivs
    fa = str(os.path.join(oddir, a))
    fb = str(os.path.join(oddir, b))

    m1 = Node.LoadFile(fa)
    m2 = Node.LoadFile(fb)

    a, b = shave_equal(m1, m2, ignore=("Description", "IndexOrder"))
    assert a == b
