import sys
import os
import glob
import difflib
import pytest

import objdictgen.node


HERE = os.path.split(__file__)[0]

# Location of the test OD files
REF = os.path.join(HERE, 'od')

# Make a list of all .od files in tests/od
ODFILES = [
    os.path.abspath(f.replace('.od', '')) for f in glob.glob(os.path.join(REF, '*.od'))
]
if os.path.exists(os.path.join(REF, 'extra')):
    ODFILES.extend([
        os.path.abspath(f.replace('.od', '')) for f in glob.glob(os.path.join(REF, 'extra', '*.od'))
    ])


@pytest.fixture
def basepath():
    """ Fixture returning the base of the project """
    return os.path.abspath(os.path.join(HERE, '..'))


@pytest.fixture
def wd(tmp_path):
    """ Fixture that changes the working directory to a temp location """
    cwd = os.getcwd()
    os.chdir(str(tmp_path))
    print("PATH: %s" % os.getcwd())
    yield os.getcwd()
    os.chdir(str(cwd))


@pytest.fixture
def profile(monkeypatch):
    """ Fixture that monkeypatches the profile load directory to include the OD directory
        for testing
    """
    newdirs = [REF]
    newdirs.extend(objdictgen.node.PROFILE_DIRS)
    monkeypatch.setattr(objdictgen.node, 'PROFILE_DIRS', newdirs)
    yield None


@pytest.fixture
def odfile(request, wd, profile):
    """ Fixture for each of the od files in the test directory """
    yield request.param


def pytest_generate_tests(metafunc):
    if "odfile" in metafunc.fixturenames:
        metafunc.parametrize("odfile", ODFILES, indirect=True)


def diff(a, b, predicate=None, **kw):
    if predicate is None:
        predicate = lambda x: True
    print(a, b)
    with open(a, 'r') as f:
        da = [n.rstrip() for n in f if predicate(n)]
    with open(b, 'r') as f:
        db = [n.rstrip() for n in f if predicate(n)]
    out = tuple(difflib.unified_diff(da, db, **kw))
    if out:
        print('\n'.join(o.rstrip() for o in out))
    return not out


class Fn:
    @staticmethod
    def diff(*a, **kw):
        return diff(*a, **kw)


@pytest.fixture
def fn():
    return Fn
