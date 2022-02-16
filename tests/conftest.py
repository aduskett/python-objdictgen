import sys
import os
import glob
import difflib
import shutil
import pytest


HERE = os.path.split(__file__)[0]
REF = os.path.join(HERE, '..', 'examples')

REF = 'od-ref'
if sys.version_info[0] >= 3:
    DUT = 'od-test3'
else:
    DUT = 'od-test2'

for f in glob.glob(os.path.join(DUT, '*')):
    os.remove(f)

for f in glob.glob(os.path.join(REF, '*.od')):
    shutil.copy(f, DUT)

ODFILES = [
    f.replace('.od', '') for f in glob.glob(os.path.join(DUT, '*.od'))
]


def pytest_generate_tests(metafunc):
    if "odfile" in metafunc.fixturenames:
        metafunc.parametrize("odfile", ODFILES)


def diff(a, b, predicate=None, **kw):
    if predicate is None:
        predicate = lambda x: True
    with open(a, 'r') as f:
        da = [n.rstrip() for n in f if predicate(n)]
    with open(b, 'r') as f:
        db = [n.rstrip() for n in f if predicate(n)]
    return difflib.unified_diff(da, db, **kw)


def diff_ref(a, b=None, **kw):
    if b is None:
        b = a
    return diff(b.replace(DUT, REF), a, **kw)


class Helpers:
    DUT = DUT
    REF = REF
    @staticmethod
    def diff(*a, **kw):
        return diff(*a, **kw)
    @staticmethod
    def diff_ref(*a, **kw):
        return diff_ref(*a, **kw)


@pytest.fixture
def fn():
    return Helpers


class Tempdir(object):

    def __init__(self, path):
        self.path = path

    @staticmethod
    def wrdata(f, d):
        with open(f, 'w') as fd:
            if d:
                fd.write(d)

    @staticmethod
    def chmod(*args, **kwargs):
        return os.chmod(*args, **kwargs)

    @staticmethod
    def makedirs(*args, **kwargs):
        return os.makedirs(*args, **kwargs)


@pytest.fixture
def wd(tmpdir):
    dir = os.getcwd()
    os.chdir(tmpdir)
    print(os.getcwd())
    print()
    yield Tempdir(tmpdir)
    os.chdir(dir)
