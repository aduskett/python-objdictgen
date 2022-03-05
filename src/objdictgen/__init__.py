import os

__version__ = "3.1"

SCRIPT_DIRECTORY = os.path.split(__file__)[0]

PROFILE_DIRECTORY = os.path.join(SCRIPT_DIRECTORY, 'config')

SCHEMA_FILE = os.path.join(SCRIPT_DIRECTORY, 'schema', 'od.schema.json')


def dbg(msg):  # pylint: disable=unused-argument
    print(">> %s" % (msg,))
