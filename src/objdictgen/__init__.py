#
#    Copyright (C) 2022  Svein Seldal, Laerdal Medical AS
#
#    This library is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    License as published by the Free Software Foundation; either
#    version 2.1 of the License, or (at your option) any later version.
#
#    This library is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with this library; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
#    USA

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
