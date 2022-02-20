import os
import shutil

from objdictgen.nodemanager import NodeManager
from objdictgen.nodelist import NodeList


BASE = os.path.join(os.path.split(__file__)[0], '..')


def test_nodelist_create():
    """ Create a new nodelist project """

    shutil.rmtree('tmp.test', True)
    os.mkdir('tmp.test')

    manager = NodeManager()
    nodelist = NodeList(manager)

    nodelist.LoadProject('tmp.test')
    nodelist.SaveProject()


def test_nodelist_load():
    """ Open an existing nodelist """

    manager = NodeManager()
    nodelist = NodeList(manager)

    nodelist.LoadProject('tmp.test')

