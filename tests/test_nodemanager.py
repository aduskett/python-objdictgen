from pprint import pprint
import os
from objdictgen.nodemanager import NodeManager


BASE = os.path.join(os.path.split(__file__)[0], '..')

def test_create_master():

    m1 = NodeManager()
    m1.CreateNewNode("TestMaster", 0x00, "master", "Longer description", "None", None, "Heartbeat", ["DS302", "GenSYNC", "Emergency"])
    m1.CloseCurrent()


def test_create_slave():

    m1 = NodeManager()
    m1.CreateNewNode("TestSlave", 0x01, "slave", "Longer description", "None", None, "Heartbeat", ["DS302", "GenSYNC", "Emergency"])
    m1.CloseCurrent()


def test_load():

    m1 = NodeManager()
    m1.OpenFileInCurrent(os.path.join(BASE, 'examples', 'example.od'))
