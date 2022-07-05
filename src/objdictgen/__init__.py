import os
import logging

log = logging.getLogger('objdictgen')

__version__ = "3.1"

SCRIPT_DIRECTORY = os.path.split(__file__)[0]

PROFILE_DIRECTORIES = [os.path.join(SCRIPT_DIRECTORY, 'config')]
odgdir = os.environ.get('ODG_PROFILE_DIR')
if odgdir:
    PROFILE_DIRECTORIES.append(odgdir)

SCHEMA_FILE = os.path.join(SCRIPT_DIRECTORY, 'schema', 'od.schema.json')


def dbg(msg):  # pylint: disable=unused-argument
    log.debug(">> %s" % (msg,))
warning = log.warning
