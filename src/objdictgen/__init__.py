import os

__version__ = "3.1"

SCRIPT_DIRECTORY = os.path.split(__file__)[0]


def dbg(msg):  # pylint: disable=unused-argument
    print(">> %s" % (msg,))
