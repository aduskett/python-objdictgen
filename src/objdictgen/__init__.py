import os
import logging

log = logging.getLogger('objdictgen')

ODG_PROGRAM = "odg"
ODG_VERSION = "3.2"

SCRIPT_DIRECTORY = os.path.split(__file__)[0]

PROFILE_DIRECTORIES = [os.path.join(SCRIPT_DIRECTORY, 'config')]
odgdir = os.environ.get('ODG_PROFILE_DIR')
if odgdir:
    PROFILE_DIRECTORIES.append(odgdir)

def dbg(msg):  # pylint: disable=unused-argument
    log.debug(">> %s", msg)
warning = log.warning
